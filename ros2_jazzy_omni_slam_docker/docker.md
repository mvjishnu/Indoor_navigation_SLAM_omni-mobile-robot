# ROS 2 Jazzy + Gazebo Harmonic — Indoor Omni SLAM

Container stack for the indoor navigation / SLAM omni (mecanum) mobile robot.

## Files

- `Dockerfile` — Ubuntu 24.04 ARM64/AMD64 image with ROS 2 Jazzy + Gazebo Harmonic.
- `docker-compose.yml` — host networking, X11/XWayland or native Wayland, optional GPU acceleration, serial/video devices, non-root user.
- `packages.yml` — required package list.
- `build.sh` — builds the image using your host UID/GID.
- `run.sh` — detects the desktop socket, route interface, and available GPU, then starts the container and opens a shell.
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

## Hyprland graphics

Run `./run.sh` from a terminal in the Hyprland session. Gazebo's Qt build in
this image has no Wayland platform plugin, so the container uses Hyprland's
XWayland display. This is set inside the container and does not change Qt
behavior for desktop applications. The compose file requests the host NVIDIA
GPU through Docker's NVIDIA container runtime; `gpus: all` requires the NVIDIA
Container Toolkit. Gazebo Transport is bound to loopback because Wi-Fi
multicast discovery prevented the local GUI from finding its simulation
server. ROS 2 continues to use host networking for communication with other
devices; CycloneDDS is pinned to the host's active `wlan0` interface for local
and LAN discovery. Host render nodes are also exposed for Mesa/DRI applications.

If NVIDIA GPU passthrough is unavailable, Gazebo may still launch using the
host's DRI/Mesa path; CUDA workloads require NVIDIA passthrough.

## ROS 2 workspace

The host project's `../src` directory is mounted as:

```text
/home/omni_robot/ros2_ws/src
```

so source changes persist outside the container.

Colcon's `build`, `install`, and `log` directories are stored in the host
project's ignored `.ros2_ws` directory, so rebuilding the container preserves
the compiled workspace.

Build your workspace inside the container:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```
# Host portability

The launcher is intended to work from Linux desktop sessions using X11,
XWayland, or native Wayland, and does not require an NVIDIA GPU. It uses the
host's DRI devices when available and otherwise allows Mesa software rendering.
NVIDIA acceleration is enabled only when both `nvidia-smi` and Docker's NVIDIA
runtime are available. For ROS 2 discovery it selects the host's default-route
network interface each time it starts.

The host still needs Docker Compose, a running desktop session, and compatible
host graphics drivers. Native Wayland needs the Qt Wayland plugin in the image;
X11/XWayland works through the mounted X socket. If display or GPU mounts change
after a container was created, recreate that container for the new mounts.
