
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

from mecanum_bot.robot_description import load_robot_description


def generate_launch_description():
    pkg_share = get_package_share_directory('mecanum_bot')
    gz_share = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(
        pkg_share, 'worlds', 'empty.sdf'
    )
    gazebo_launch_file = os.path.join(
        gz_share, 'launch', 'gz_sim.launch.py'
    )

    # Patch the controller parameter path at runtime so this launch does not
    # depend on the source-tree path embedded in the original URDF.
    robot_description = load_robot_description(sim=True)

    gazebo_resources = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.dirname(pkg_share),
        separator=os.pathsep,
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch_file),
        launch_arguments={
            'gz_args': f'-r -v 4 {world_file}'
        }.items(),
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            # Passive roller joints -> /joint_states so rollers appear in TF/RViz.
            '/roller_joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            # View-only camera (not used by navigation).
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        remappings=[('/roller_joint_states', '/joint_states')],
        output='screen',
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
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
        ],
        output='screen',
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager',
            '/controller_manager',
            '--controller-manager-timeout',
            '60',
        ],
        output='screen',
    )

    mecanum_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'mecanum_drive_controller',
            '--controller-manager',
            '/controller_manager',
            '--controller-manager-timeout',
            '60',
        ],
        output='screen',
    )

    teleop_keyboard = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        prefix=(
            'xterm -fa "Monospace" -fs 10 '
            '-geometry 65x20+50+50 -e'
        ),
        remappings=[
            (
                '/cmd_vel',
                '/mecanum_drive_controller/reference',
            ),
        ],
        parameters=[
            {'stamped': True},
        ],
        output='screen',
    )

    return LaunchDescription([
        gazebo_resources,
        gazebo,
        clock_bridge,
        robot_state_publisher,
        TimerAction(
            period=2.0,
            actions=[spawn_robot],
        ),
        TimerAction(
            period=4.0,
            actions=[joint_state_broadcaster_spawner],
        ),
        TimerAction(
            period=6.0,
            actions=[mecanum_controller_spawner],
        ),
        teleop_keyboard,
    ])
