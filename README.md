# Indoor_navigation_SLAM_omni-mobile-robot
An autonomous ROS 2 Jazzy-based indoor omni-directional mobile robot featuring mecanum drive, LiDAR-based SLAM, sensor fusion, Nav2 autonomous navigation, and MCU-based motor and encoder control.

## Indoor simulation

Build the ROS workspace in the Jazzy container, then start mapping and navigation:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch mecanum_bot navigation.launch.py teleop:=true
```

The default launch uses live SLAM. Use the keyboard teleop window to explore;
then use the RViz goal tool to navigate. To map without Nav2, use
`ros2 launch mecanum_bot slam.launch.py`.

Save a map before using AMCL localization:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/indoor
ros2 launch mecanum_bot navigation.launch.py slam:=false map:=$(realpath ~/ros2_ws/indoor.yaml)
```

`slam:=false` requires an existing map YAML file. For headless simulation, pass
`headless:=true rviz:=false teleop:=false`.
