"""
Simulation and EKF with Nav2, using live SLAM or AMCL localization.

slam:=true (default) maps while navigating. slam:=false localizes with AMCL on
a saved map: the packaged maps/warehouse.yaml by default, or map:=PATH.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Build the navigation launch description."""
    pkg_share = get_package_share_directory('mecanum_bot')
    slam_share = get_package_share_directory('slam_toolbox')

    params_file = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    slam = LaunchConfiguration('slam')
    use_sim_time = ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)
    sim_time = {'use_sim_time': use_sim_time}

    declare_args = [
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument(
            'slam', default_value='true',
            description='true: build the map; false: localize on the map argument'),
        DeclareLaunchArgument(
            'map', default_value=os.path.join(pkg_share, 'maps', 'warehouse.yaml'),
            description='saved map yaml used when slam:=false'),
        DeclareLaunchArgument('world', default_value=os.path.join(
            pkg_share, 'worlds', 'warehouse.sdf')),
        DeclareLaunchArgument('world_name', default_value='warehouse'),
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('teleop', default_value='false'),
    ]

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'sim_base.launch.py')),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'world_name': LaunchConfiguration('world_name'),
            'headless': LaunchConfiguration('headless'),
        }.items(),
    )

    # ---- map source: live SLAM ... -------------------------------------------------
    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_share, 'launch', 'online_async_launch.py')),
        launch_arguments={
            'slam_params_file': os.path.join(
                pkg_share, 'config', 'slam_toolbox_mapping.yaml'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }.items(),
        condition=IfCondition(slam),
    )

    # ---- ... or a saved map + AMCL ------------------------------------------------------
    localization = GroupAction(
        condition=UnlessCondition(slam),
        actions=[
            Node(package='nav2_map_server', executable='map_server',
                 name='map_server', output='screen',
                 parameters=[params_file, sim_time,
                             {'yaml_filename': LaunchConfiguration('map')}]),
            Node(package='nav2_amcl', executable='amcl', name='amcl',
                 output='screen', parameters=[params_file, sim_time]),
            Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
                 name='lifecycle_manager_localization', output='screen',
                 parameters=[sim_time, {'autostart': True,
                                        'node_names': ['map_server', 'amcl']}]),
        ],
    )

    # ---- Nav2 servers ---------------------------------------------------------------------
    odom_remap = ('odom', '/odometry/filtered')
    nav_nodes = [
        Node(package='nav2_controller', executable='controller_server',
             name='controller_server', output='screen',
             parameters=[params_file, sim_time],
             remappings=[odom_remap, ('cmd_vel', 'cmd_vel_nav')]),
        Node(package='nav2_smoother', executable='smoother_server',
             name='smoother_server', output='screen',
             parameters=[params_file, sim_time]),
        Node(package='nav2_planner', executable='planner_server',
             name='planner_server', output='screen',
             parameters=[params_file, sim_time]),
        Node(package='nav2_behaviors', executable='behavior_server',
             name='behavior_server', output='screen',
             parameters=[params_file, sim_time],
             remappings=[odom_remap, ('cmd_vel', 'cmd_vel_nav')]),
        Node(package='nav2_bt_navigator', executable='bt_navigator',
             name='bt_navigator', output='screen',
             parameters=[params_file, sim_time],
             remappings=[odom_remap]),
        Node(package='nav2_waypoint_follower', executable='waypoint_follower',
             name='waypoint_follower', output='screen',
             parameters=[params_file, sim_time]),
        Node(package='nav2_velocity_smoother', executable='velocity_smoother',
             name='velocity_smoother', output='screen',
             parameters=[params_file, sim_time],
             remappings=[odom_remap, ('cmd_vel', 'cmd_vel_nav'),
                         ('cmd_vel_smoothed', 'cmd_vel')]),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_navigation', output='screen',
             parameters=[sim_time, {
                 'autostart': True,
                 'node_names': ['controller_server', 'smoother_server',
                                'planner_server', 'behavior_server',
                                'bt_navigator', 'waypoint_follower',
                                'velocity_smoother'],
             }]),
    ]

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(pkg_share, 'config', 'nav_slam.rviz')],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen',
    )

    teleop_keyboard = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        prefix="xterm -fa 'Monospace' -fs 10 -geometry 65x20+50+50 -e",
        remappings=[('/cmd_vel', '/mecanum_drive_controller/reference')],
        parameters=[{'stamped': True}],
        condition=IfCondition(LaunchConfiguration('teleop')),
        output='screen',
    )

    return LaunchDescription(
        declare_args + [sim, slam_toolbox, localization] + nav_nodes
        + [rviz, teleop_keyboard])
