# Indoor_navigation_SLAM_omni-mobile-robot
An autonomous ROS 2 Jazzy-based indoor omni-directional mobile robot featuring mecanum drive, LiDAR-based SLAM, sensor fusion, Nav2 autonomous navigation, and MCU-based motor and encoder control.

The simulation runs in Docker (ROS 2 Jazzy + Gazebo Harmonic). The guide below takes you from a fresh Linux machine to mapping a warehouse with SLAM, saving the map, and navigating with **2D Goal Pose** and **waypoints**.

---

## Contents

1. [Install Docker](#1-install-docker)
2. [(Optional) NVIDIA GPU support](#2-optional-nvidia-gpu-support)
3. [Get the project](#3-get-the-project)
4. [Build and start the container](#4-build-and-start-the-container)
5. [Build the ROS workspace](#5-build-the-ros-workspace)
6. [Map the warehouse with SLAM](#6-map-the-warehouse-with-slam)
7. [Save the map](#7-save-the-map)
8. [Navigate on the saved map: 2D Goal Pose and waypoints](#8-navigate-on-the-saved-map)
9. [Stop everything](#9-stop-everything)
10. [Troubleshooting](#10-troubleshooting)
11. [Project reference](#project-reference)

---

## 1. Install Docker

You need a **Linux** host (x86_64 or arm64) with a desktop session (X11 or Wayland). Pick your distribution:

**Ubuntu / Debian / Linux Mint / Pop!_OS**
```bash
sudo apt update
sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh        # Docker Engine + Compose plugin
```

**Arch / Manjaro / CachyOS / EndeavourOS**
```bash
sudo pacman -S --needed docker docker-compose docker-buildx git
```

**Fedora**
```bash
sudo dnf install -y dnf-plugins-core git
sudo dnf config-manager addrepo --from-repofile=https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-buildx-plugin
```

Then, on **every** distribution:
```bash
sudo systemctl enable --now docker      # start Docker now and at boot
sudo usermod -aG docker $USER           # run docker without sudo
```
**Log out and back in** (or reboot) so the group change applies. Check it works:
```bash
docker run --rm hello-world
docker compose version
```

> `docker buildx` is recommended but optional. Without it, the project falls back to Docker's classic builder automatically.

## 2. (Optional) NVIDIA GPU support

Skip this if you have Intel/AMD graphics or an iGPU: those work out of the box through Mesa.
With an NVIDIA card, install the NVIDIA driver and then the
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html):
```bash
# after installing the nvidia-container-toolkit package for your distro:
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```
`run.sh` detects the toolkit and enables the GPU automatically.

## 3. Get the project

```bash
cd ~
git clone https://github.com/mvjishnu/Indoor_navigation_SLAM_omni-mobile-robot.git
cd Indoor_navigation_SLAM_omni-mobile-robot
```

## 4. Build and start the container

```bash
cd ros2_jazzy_omni_slam_docker
./run.sh
```

- The **first run builds the image**, which takes 10–20 minutes and downloads about 4 GB. Later runs start in seconds.
- `run.sh` detects the following automatically:
  - your user ID;
  - your display (X11, XWayland or Wayland);
  - your GPU;
  - the serial and camera device groups.
- It ends with a shell **inside the container**. The prompt looks like `omni_robot@indoor_slam:~/ros2_ws$`.
- **Run `./run.sh` again in another terminal** whenever you need another container shell. It joins the same running container.

Useful options: `./run.sh --build` (rebuild after changing `Dockerfile` or `packages.yml`), `./run.sh --no-gpu`.
Details: [ros2_jazzy_omni_slam_docker/docker.md](ros2_jazzy_omni_slam_docker/docker.md).

## 5. Build the ROS workspace

Inside the container:
```bash
cb
```
`cb` is a shortcut for `cd ~/ros2_ws && colcon build --symlink-install && source install/setup.bash`.
Run it again whenever you change files in `src/`.

## 6. Map the warehouse with SLAM

**Terminal 1** (container):
```bash
ros2 launch mecanum_bot navigation.launch.py teleop:=true
```

Three windows open:

| Window | What it is |
|---|---|
| **Gazebo** | The 20 × 15 m warehouse simulation, with the robot spawned on the main walkway |
| **RViz** | The map being built, the robot, lidar scan, costmaps, the Navigation 2 panel and the **Robot Camera** view (top-left; drag to resize or undock) |
| **xterm (teleop)** | Keyboard driving |

Build the map by driving the robot around. You can drive it two ways.

**A. With the keyboard.** Click the small xterm window so it has focus, then:

| Key | Motion |
|---|---|
| `i` / `,` | forward / backward |
| `j` / `l` | rotate left / right |
| `Shift` + `J` / `L` | **strafe** left / right (mecanum sideways motion) |
| `Shift` + `U` `O` `M` `>` | **diagonal** strafing (mecanum) |
| `u` `o` `m` `.` | curved moves (drive + turn) |
| `k` | stop |
| `q` / `z` | faster / slower |

**B. With Nav2 goals.** In RViz, click **2D Goal Pose**, then click and drag on a free (white) part of the map, as described in [step 8](#8-navigate-on-the-saved-map). With live SLAM, goals must be inside the area already mapped.

Tips for a clean map:
- **Drive slowly and avoid bumping into things.** Wheel slip from collisions corrupts the map.
- Pass every area once, and turn the robot so the lidar sees each wall.
- Watch RViz: the map should have straight, single walls. Doubled or skewed walls mean the robot slipped. If that happens, stop and start mapping again.

## 7. Save the map

Keep the mapping launch running. Open a **second container shell** (on the host: `./run.sh`) and run:

```bash
cd ~/ros2_ws/src/mecanum_bot/maps
ros2 run nav2_map_server map_saver_cli -f warehouse --ros-args -p use_sim_time:=true
cb
```

This writes `warehouse.pgm` (the image) and `warehouse.yaml` (its metadata) into `src/mecanum_bot/maps/`. That folder is on your host, so the map survives container restarts. `cb` then installs it.
To keep several maps, use another name, e.g. `-f warehouse_v2`.

Then stop the mapping launch with **Ctrl+C** in terminal 1.

## 8. Navigate on the saved map

**Terminal 1** (container):
```bash
ros2 launch mecanum_bot navigation.launch.py slam:=false
```
This loads `maps/warehouse.yaml` and localizes the robot with **AMCL**.
To use another map: `ros2 launch mecanum_bot navigation.launch.py slam:=false map:=$HOME/ros2_ws/src/mecanum_bot/maps/warehouse_v2.yaml`.

Wait until the **Navigation 2** panel in RViz shows **Navigation: active** and **Localization: active**.

### 8.1 Set the starting pose (2D Pose Estimate)

AMCL starts with the robot at the origin, which is where it spawns. If the robot is somewhere else, or the lidar scan (red dots) doesn't line up with the map walls:
1. Click **2D Pose Estimate** in the RViz toolbar.
2. Click the robot's real position on the map, and **drag** in the direction it faces. Then release.
3. The red scan dots should snap onto the walls. Drive a little if needed; AMCL refines its estimate as the robot moves.

### 8.2 Send a goal (2D Goal Pose)

1. Click **2D Goal Pose** in the RViz toolbar.
2. Click the destination on a free (white) area of the map, then **drag** to set the final heading (the arrow direction). Release.
3. The robot plans a path (green line) and drives there. Being a mecanum robot, it **moves and rotates at the same time**. It strafes and drives diagonally where useful, and finishes facing the arrow direction.

Click a new goal at any time to replace the current one. The **Cancel** button in the Navigation 2 panel stops the robot.

### 8.3 Follow several goal points (waypoints)

**From RViz:**
1. In the **Navigation 2** panel, click **Waypoint / Nav Through Poses Mode**.
2. Select the **Nav2 Goal** tool in the toolbar and click-drag each waypoint on the map, in order. Each one appears as a numbered arrow.
3. Click **Start Waypoint Following**. The robot visits each point in turn.

**From the command line:**
```bash
ros2 action send_goal /follow_waypoints nav2_msgs/action/FollowWaypoints "{poses: [
  {header: {frame_id: map}, pose: {position: {x: 2.5, y: 0.3},  orientation: {w: 1.0}}},
  {header: {frame_id: map}, pose: {position: {x: 1.5, y: 2.65}, orientation: {w: 1.0}}},
  {header: {frame_id: map}, pose: {position: {x: -3.0, y: 0.3}, orientation: {w: 1.0}}},
  {header: {frame_id: map}, pose: {position: {x: 0.0, y: 0.0},  orientation: {w: 1.0}}}]}"
```

## 9. Stop everything

- **Ctrl+C** in the launch terminal stops the simulation.
- `exit` leaves a container shell.
- On the host, `./stop.sh` (in `ros2_jazzy_omni_slam_docker/`) stops and removes the container. Your code, build and maps are kept.

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| `permission denied ... docker.sock` | You're not in the `docker` group yet. Run `sudo usermod -aG docker $USER`, then **log out and back in**. |
| Gazebo or RViz window doesn't open | Start `./run.sh` from a terminal inside your desktop session. On plain X11, also try `xhost +local:`. |
| Everything moves in slow motion | Gazebo runs slower than real time on weaker CPUs (check the % at the bottom of Gazebo). Speeds are correct in simulation time. Close other heavy programs. |
| Robot doesn't move to a goal | Make sure the goal is on white (free) map space, and Navigation 2 shows *active*. With `slam:=false`, check the scan lines up with the map, or redo **2D Pose Estimate**. |
| "Start occupied" / robot stuck | The map has an obstacle where the robot is, usually from a bad map. Re-map slowly ([step 6](#6-map-the-warehouse-with-slam)) and save again. |
| `colcon` permission errors | Run `./run.sh` again on the host. It fixes ownership of the build folders. |
| Changed `Dockerfile` / `packages.yml` | `./run.sh --build` |

---

## Project reference

### Layout
| Path | Purpose |
|---|---|
| `ros2_jazzy_omni_slam_docker/` | Docker image, `run.sh` / `build.sh` / `stop.sh`, and [docker.md](ros2_jazzy_omni_slam_docker/docker.md) |
| `src/mecanum_bot/launch/` | `navigation.launch.py` (SLAM or AMCL + Nav2), `slam.launch.py` (mapping only), `sim_base.launch.py` (Gazebo, ros2_control, EKF) |
| `src/mecanum_bot/config/` | `nav2_params.yaml`, `ekf.yaml`, `slam_toolbox_mapping.yaml`, `controllers_nav.yaml`, `nav_slam.rviz` |
| `src/mecanum_bot/maps/` | Saved maps (`warehouse.yaml` is the default for `slam:=false`) |
| `src/mecanum_bot/worlds/` | `warehouse.sdf` (default) and `indoor_house.sdf` |
| `src/mecanum_bot/tools/gen_warehouse.py` | Generates `warehouse.sdf`. Edit it and run `python3 tools/gen_warehouse.py` to change the world |
| `mcu_encoder_mecanum/` | MCU firmware for motors and encoders (PlatformIO) |

### Launch arguments (`navigation.launch.py`)
| Argument | Default | Meaning |
|---|---|---|
| `slam` | `true` | `true` = build a map with SLAM Toolbox; `false` = AMCL on a saved map |
| `map` | `maps/warehouse.yaml` | Map used when `slam:=false` |
| `teleop` | `false` | Open the keyboard teleop window |
| `rviz` | `true` | Start RViz |
| `headless` | `false` | Run Gazebo without its GUI |
| `world`, `world_name` | warehouse | Gazebo world file and its `<world name>` |

### Navigation stack
- **Sensor fusion:** a `robot_localization` EKF fuses wheel odometry (vx, vy, yaw rate) with the IMU gyro (yaw rate). It outputs `odom → base_footprint` and `/odometry/filtered`.
- **Localization:** SLAM Toolbox while mapping; AMCL (omni motion model) on a saved map.
- **Planner:** Smac 2D (A*). It is cost-aware, so paths stay centred in doorways and aisles.
- **Controller:** DWB, sampling holonomic `vx, vy, wz` trajectories:
  - footprint-aware collision checking (no corner cutting in doorways);
  - path-following critics drive the robot in any direction;
  - moderate heading critics rotate it while it translates;
  - the final heading comes from the 2D Goal Pose arrow.
- **Limits:** 0.34 m/s in any direction, 1.08 rad/s rotation.
- **Camera:** a forward-facing 640 x 360, 15 Hz view camera on `camera_link`, published as `/camera/image_raw` and `/camera/camera_info`. It's for viewing only; navigation doesn't use it.
- **Inflation:** 0.45 m radius with a steep fall-off, tuned for 0.9–1.2 m passages.

