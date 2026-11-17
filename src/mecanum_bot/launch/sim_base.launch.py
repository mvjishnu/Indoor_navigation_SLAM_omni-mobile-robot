"""
Simulation layer: Gazebo world, robot, ros2_control, sensors, EKF, and cmd_vel stamper.

This does not touch the existing bot.launch.py.  SLAM and navigation launch files
include this one and add their own nodes on top.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

from mecanum_bot.robot_description import load_robot_description


def generate_launch_description():
    """Build the simulation launch description."""
    pkg_share = get_package_share_directory('mecanum_bot')
    gz_share = get_package_share_directory('ros_gz_sim')

    world = LaunchConfiguration('world')
    world_name = LaunchConfiguration('world_name')
    headless = LaunchConfiguration('headless')

    robot_description = load_robot_description(sim=True)

    declare_args = [
        DeclareLaunchArgument(
            'world',
            default_value=os.path.join(pkg_share, 'worlds', 'indoor_house.sdf'),
            description='SDF world file'),
        DeclareLaunchArgument(
            'world_name', default_value='indoor_house',
            description='<world name="..."> inside the SDF file'),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='true = run Gazebo server only (no GUI)'),
    ]

    gazebo_resources = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.dirname(pkg_share),
        separator=os.pathsep,
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gz_share, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': [
                PythonExpression(
                    ["'-s ' if '", headless, "' == 'true' else ''"]),
                '-r -v 2 ', world,
            ],
        }.items(),
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            # Passive roller joints (wheel joints come from joint_state_broadcaster).
            '/roller_joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        remappings=[('/imu', '/imu/data'),
                    ('/roller_joint_states', '/joint_states')],
        output='screen',
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'robot_description': ParameterValue(robot_description, value_type=str),
            'use_sim_time': True,
        }],
        output='screen',
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'omni_mobile_bot',
            '-world', world_name,
            '-x', '0.0', '-y', '0.0', '-z', '0.01',
        ],
        output='screen',
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
        output='screen',
    )

    mecanum_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'mecanum_drive_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
        output='screen',
    )

    # Wheel odometry + IMU gyro -> /odometry/filtered and odom -> base_footprint TF.
    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[
            os.path.join(pkg_share, 'config', 'ekf.yaml'),
            {'use_sim_time': True},
        ],
        remappings=[
            ('/wheel/odometry', '/mecanum_drive_controller/odometry'),
        ],
    )

    # Nav2 publishes Twist on /cmd_vel; the controller wants TwistStamped.
    cmd_vel_stamper = Node(
        package='mecanum_bot',
        executable='cmd_vel_stamper',
        name='cmd_vel_stamper',
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    return LaunchDescription(declare_args + [
        gazebo_resources,
        gazebo,
        bridge,
        robot_state_publisher,
        spawn_robot,
        RegisterEventHandler(OnProcessExit(
            target_action=spawn_robot,
            on_exit=[joint_state_broadcaster_spawner])),
        RegisterEventHandler(OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[mecanum_controller_spawner])),
        ekf,
        cmd_vel_stamper,
    ])
