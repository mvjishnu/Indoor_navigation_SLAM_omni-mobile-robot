# RPLIDAR C1 test on Raspberry Pi 4

Run these commands **on the Pi**, with the C1 connected through its powered USB
adapter. This test runs independently of ROS and the robot's motors.

```bash
cd testing
sudo apt update
sudo apt install -y git build-essential
chmod +x lidar_c1.sh
./lidar_c1.sh --list
./lidar_c1.sh /dev/ttyUSB0
```

Use the port shown by `--list` if it differs. A `/dev/serial/by-id/...` path stays
stable when other USB devices are attached. The default baud rate is **460800**
for C1; an optional second argument overrides it.

On first run, the launcher downloads the
[official SLAMTEC SDK](https://github.com/Slamtec/rplidar_sdk) into
`testing/.rplidar_sdk/` and compiles its native `ultra_simple` executable on the Pi.
Internet is needed for the initial download. To build before connecting the sensor:

```bash
./lidar_c1.sh --setup
```

Successful communication prints the sensor serial number, firmware/hardware
versions, and health status, followed by live `theta` (degrees), `Dist`
(millimetres), and `Q` (return quality) readings. Confirm that nonzero distances
change when you move a target in view. Zero distances can represent invalid
returns. Press **Ctrl+C** to stop scanning and stop the motor. The vendor demo's
exit code is not a pass/fail verdict: inspect its output and live readings.

If access is denied:

```bash
sudo usermod -aG dialout "$USER"
```

Log out and back in before retrying. If no port appears, check USB power and the
data cable, and inspect `sudo dmesg | tail -30`. If communication times out, stop
any ROS LiDAR driver or other program using that port, verify the port and 460800
baud rate, and check the USB adapter and power supply.

References: [C1 datasheet (baud rate)](https://www.slamtec.ai/wp-content/uploads/2024/09/SLAMTEC_rplidar_datasheet_C1_v1.1_en.pdf),
[vendor scan demo (arguments and output)](https://github.com/Slamtec/rplidar_sdk/blob/master/app/ultra_simple/main.cpp).
