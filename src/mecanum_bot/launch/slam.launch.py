"""Simulation + EKF + SLAM Toolbox mapping + RViz (+ keyboard teleop to drive and map)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Build the mapping launch description."""
    pkg_share = get_package_share_directory('mecanum_bot')
    slam_share = get_package_share_directory('slam_toolbox')

    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_args = [
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('world', default_value=os.path.join(
            pkg_share, 'worlds', 'warehouse.sdf')),
        DeclareLaunchArgument('world_name', default_value='warehouse'),
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('teleop', default_value='true'),
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

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_share, 'launch', 'online_async_launch.py')),
        launch_arguments={
            'slam_params_file': os.path.join(
                pkg_share, 'config', 'slam_toolbox_mapping.yaml'),
            'use_sim_time': use_sim_time,
        }.items(),
    )

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

    return LaunchDescription(declare_args + [sim, slam, rviz, teleop_keyboard])
