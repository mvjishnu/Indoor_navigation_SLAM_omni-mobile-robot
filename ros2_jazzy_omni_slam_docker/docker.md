# ROS 2 Jazzy + Gazebo Harmonic — Indoor Omni SLAM

Container stack for the indoor navigation / SLAM omni (mecanum) mobile robot.

## Files

- `Dockerfile` — Ubuntu 24.04 ARM64/AMD64 image with ROS 2 Jazzy + Gazebo Harmonic.
- `docker-compose.yml` — host networking, X11, serial/video devices, non-root user.
- `packages.yml` — required package list.
- `build.sh` — builds the image using your host UID/GID.
- `run.sh` — starts the container and opens a new shell.
- `stop.sh` — stops/removes the container.
- `workspace/` — your ROS 2 workspace.

## First run

```bash
chmod +x build.sh run.sh stop.sh
./build.sh
./run.sh
```

Inside the container:

```bash
ros2 --version
gz sim --versions
ros2 pkg list | grep -E 'nav2|slam_toolbox|ros_gz'
```

## Important Raspberry Pi note

Use **64-bit Raspberry Pi OS**. ROS 2 Jazzy has Tier-1 ARM64 binaries for Ubuntu Noble, and ROS 2 documents Raspberry Pi OS 64-bit + Docker as a supported route.

Gazebo Harmonic and RViz2 are included because this same image can be used for simulation/development, but a Raspberry Pi 4 with 4 GB RAM is not an ideal Gazebo/RViz workstation. For the physical robot, run the ROS nodes needed by the robot and use a laptop/desktop for heavy Gazebo/RViz visualization when necessary.

## Serial MCU

The compose file passes through:

- `/dev/ttyUSB0`
- `/dev/ttyACM0`

The container user is added to `dialout`.

If your device has another path, edit `docker-compose.yml`.

## Camera

`/dev/video0` is passed through and the container user is added to `video`.

## X11

If Gazebo/RViz cannot connect to the display, on the host run:

```bash
xhost +local:docker
```

Then run:

```bash
./run.sh
```

## ROS 2 workspace

Your host `./workspace` is mounted as:

```text
/home/<user>/ros2_ws
```

so your source code persists outside the container.

Build your workspace inside the container:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```
