# ROS 2 Jazzy + Gazebo Harmonic: Indoor Omni SLAM container

## Quick start (any Linux host)

```bash
cd ros2_jazzy_omni_slam_docker
./run.sh            # first run builds the image (~10-20 min), then opens a shell
```

Inside the container:

```bash
cb                  # = cd ~/ros2_ws && colcon build --symlink-install && source install/setup.bash
ros2 launch mecanum_bot navigation.launch.py teleop:=true
```

Open more shells into the same container by running `./run.sh` again. Use `./stop.sh` to stop the container.

| Command | What it does |
|---|---|
| `./run.sh` | Detects the host, builds the image if needed, starts the container, opens a shell |
| `./run.sh --build` | Rebuilds the image first. Run this after editing `Dockerfile` or `packages.yml` |
| `./run.sh --no-gpu` | Starts without requesting the NVIDIA GPU |
| `./run.sh ros2 topic list` | Runs one command inside the container |
| `./build.sh` | Builds the image only |
| `./stop.sh` | Stops and removes the container. The image, workspace build and history are kept |

## Host requirements

- Linux (x86_64 or arm64 such as Raspberry Pi OS 64-bit or Ubuntu), with Docker Engine and Docker Compose. Your user must be in the `docker` group.
- **buildx is optional.** The Dockerfile uses only classic-builder syntax. If buildx is missing, `run.sh` falls back to the classic builder.
- GUI: X11, XWayland (GNOME, KDE, Hyprland, Sway), or native Wayland. With no display, use `headless:=true rviz:=false teleop:=false`.
- NVIDIA GPU (optional): needs `nvidia-container-toolkit` registered with Docker (`sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker`). If it is not set up, Mesa/DRI or software rendering is used.

Docker Desktop on macOS or Windows is not supported out of the box because the setup relies on host networking, `/dev` passthrough and X11 sockets. On Windows, use WSL2 with Docker Engine inside the WSL distro (WSLg provides the display).

## What `run.sh` handles for you

- **UID/GID:** the image is built with your host UID/GID, so files in `src/` and `.ros2_ws/` stay owned by you. If the image was built for a different UID, it is rebuilt automatically.
- **Workspace dirs:** creates `../.ros2_ws/{build,install,log,history}` before Docker starts. Otherwise Docker creates them as root and colcon fails. Directories left root-owned by the old setup are fixed automatically.
- **Display:** prefers X11/XWayland (`QT_QPA_PLATFORM=xcb`) because RViz2 and Gazebo are Qt5 apps and are most reliable there. It falls back to native Wayland and passes the Xauthority cookie when one exists.
- **Device groups:** detects the host's serial group (`dialout` on Debian/Ubuntu, `uucp` on Arch/Fedora), plus `video`, `render` and `input`. Access to `/dev/ttyUSB*`, `/dev/ttyACM*`, cameras, DRI and input devices goes through `device_cgroup_rules`, so hot-plugging works without `privileged`.
- **GPU:** adds `docker-compose.nvidia.yml` only when `nvidia-smi` works and Docker has the `nvidia` runtime.
- **`.env`:** writes all of the above to `.env` (gitignored), so plain `docker compose up -d` and `docker compose exec ros2 bash` also work afterwards.

## Networking (ROS 2 / DDS)

The container uses host networking with CycloneDDS. On every start, the entrypoint writes `/tmp/cyclonedds.xml` bound to the host's current default-route interface (`wlan0`, `eth0`, `enp*` and so on) plus loopback. With no network at all, it falls back to localhost-only discovery. To force an interface, run `ROS_NETWORK_INTERFACE=eth0 ./run.sh`. To use your own config, set `CYCLONEDDS_URI`. Set `ROS_DOMAIN_ID=<n> ./run.sh` to isolate the robot on a shared LAN.

Gazebo Transport is pinned to `127.0.0.1` because Wi-Fi multicast stops the Gazebo GUI from finding its server.

## Layout

| Path | Purpose |
|---|---|
| `Dockerfile` | Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic (amd64/arm64) |
| `packages.yml` | apt packages to install (one per line, `#` comments allowed) |
| `entrypoint.sh` | Fixes workspace ownership and writes the DDS config, then runs the command |
| `ros_bashrc.sh` | Shell environment: sources ROS and the workspace, Ubuntu-style colour prompt and `ls` colours, aliases `cb`, `cbr`, `sl`, `ll`, `la`, `nvrun`, history |
| `docker-compose.yml` / `docker-compose.nvidia.yml` | Runtime config and GPU overlay |
| `../src` → `~/ros2_ws/src` | Your packages (live-mounted) |
| `../.ros2_ws/{build,install,log}` | colcon outputs, kept across container rebuilds |
| `../.ros2_ws/history` | Persistent bash history |

## Troubleshooting

- **`permission denied` in build/ or install/:** run `./run.sh` again; it re-owns the directories. As a last resort, delete them with `sudo rm -rf ../.ros2_ws/{build,install,log}`.
- **GUI does not open (`could not connect to display`):** start `./run.sh` from a terminal inside your desktop session. On X11 you can also run `xhost +local:`.
- **Which GPU renders?** Check with `glxinfo -B`. Intel/AMD iGPUs and non-NVIDIA laptops use Mesa hardware acceleration through `/dev/dri` with no setup. On hybrid NVIDIA laptops the iGPU renders by default; prefix a command with `nvrun` (for example `nvrun ros2 launch mecanum_bot navigation.launch.py`) to use the dGPU. If you see a black window or glitches, use `LIBGL_ALWAYS_SOFTWARE=1 ./run.sh`.
- **Serial device not visible:** check that it shows up on the host (`ls /dev/ttyUSB* /dev/ttyACM*`). Devices plugged in after the container started appear automatically.
- **Raspberry Pi:** use a 64-bit OS. Gazebo and RViz are heavy on a Pi 4, so run the robot nodes there and visualise from a laptop on the same `ROS_DOMAIN_ID`.
