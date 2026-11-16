"""
Assemble the robot_description used by the SLAM and navigation launch files.

The original ``urdf/omni_mobile_bot.urdf`` is never modified.  Two things are
appended to it at launch time:

* a ``base_footprint`` frame that sits at the geometric centre of the four
  wheels with x pointing to the front of the robot (the camera side).  The
  mecanum controller and the EKF both assume that convention, whereas the CAD
  ``base_link`` is on a wheel corner with +y pointing forward.
* (simulation only) the Gazebo lidar and IMU sensors, modelled on the
  RPLiDAR C1 and the MPU9250 so that the simulation resembles the real parts.
"""

import math
import os
import re

PACKAGE_NAME = 'mecanum_bot'
BASE_URDF = 'omni_mobile_bot.urdf'

# RPLiDAR C1: 5000 samples/s at ~10 Hz -> 500 samples per revolution, 0.05-12 m.
LIDAR_SAMPLES = 500
LIDAR_RATE_HZ = 10
LIDAR_MIN_RANGE = 0.05
LIDAR_MAX_RANGE = 12.0

NAV_FRAMES_XML = """
  <!-- ===== navigation frames (added by mecanum_bot.robot_description) ===== -->
  <!-- base_footprint: centre of the wheel rectangle on the ground,
       x = forward (CAD base_link +y), y = left (CAD base_link -x). -->
  <link name="base_footprint"/>
  <joint name="footprint_to_root" type="fixed">
    <origin xyz="-0.1 -0.1 0" rpy="0 0 -1.5707963"/>
    <parent link="base_footprint"/>
    <child link="root"/>
  </joint>
"""


def _sensor_xml():
    min_angle = -math.pi
    max_angle = math.pi - 2.0 * math.pi / LIDAR_SAMPLES
    gyro_noise = ''.join(
        f"""
          <{axis}>
            <noise type="gaussian">
              <mean>0.0</mean><stddev>0.0015</stddev>
              <bias_mean>0.0005</bias_mean><bias_stddev>0.0002</bias_stddev>
            </noise>
          </{axis}>""" for axis in 'xyz')
    accel_noise = ''.join(
        f"""
          <{axis}>
            <noise type="gaussian">
              <mean>0.0</mean><stddev>0.03</stddev>
              <bias_mean>0.02</bias_mean><bias_stddev>0.005</bias_stddev>
            </noise>
          </{axis}>""" for axis in 'xyz')
    return f"""
  <!-- ===== simulated sensors (added by mecanum_bot.robot_description) ===== -->
  <gazebo reference="lidar_link">
    <sensor name="rplidar_c1" type="gpu_lidar">
      <!-- 1 cm above the link origin so the scan plane clears the chassis top -->
      <pose>0 0 0.01 0 0 0</pose>
      <topic>scan</topic>
      <gz_frame_id>lidar_link</gz_frame_id>
      <update_rate>{LIDAR_RATE_HZ}</update_rate>
      <always_on>true</always_on>
      <visualize>false</visualize>
      <lidar>
        <scan>
          <horizontal>
            <samples>{LIDAR_SAMPLES}</samples>
            <resolution>1</resolution>
            <min_angle>{min_angle:.6f}</min_angle>
            <max_angle>{max_angle:.6f}</max_angle>
          </horizontal>
        </scan>
        <range>
          <min>{LIDAR_MIN_RANGE}</min>
          <max>{LIDAR_MAX_RANGE}</max>
          <resolution>0.01</resolution>
        </range>
        <noise>
          <type>gaussian</type>
          <mean>0.0</mean>
          <stddev>0.01</stddev>
        </noise>
      </lidar>
    </sensor>
  </gazebo>

  <gazebo reference="imu_link">
    <sensor name="gy91_imu" type="imu">
      <topic>imu</topic>
      <gz_frame_id>imu_link</gz_frame_id>
      <update_rate>100</update_rate>
      <always_on>true</always_on>
      <imu>
        <angular_velocity>{gyro_noise}
        </angular_velocity>
        <linear_acceleration>{accel_noise}
        </linear_acceleration>
      </imu>
    </sensor>
  </gazebo>
"""


def build_robot_description(urdf_text, controllers_yaml=None, sim=True):
    """
    Return the URDF string with the navigation additions applied.

    ``controllers_yaml`` replaces the ros2_control parameter file that the
    original URDF hard-codes (simulation only).
    """
    extra = NAV_FRAMES_XML
    if sim:
        if controllers_yaml is not None:
            urdf_text, count = re.subn(
                r'<parameters>[^<]*</parameters>',
                f'<parameters>{controllers_yaml}</parameters>',
                urdf_text, count=1)
            if count != 1:
                raise RuntimeError(
                    'No <parameters> tag found in the URDF gz_ros2_control plugin')
        extra += _sensor_xml()
    index = urdf_text.rindex('</robot>')
    return urdf_text[:index] + extra + urdf_text[index:]


def load_robot_description(sim=True):
    """Read the installed URDF and return the patched robot_description."""
    from ament_index_python.packages import get_package_share_directory
    share = get_package_share_directory(PACKAGE_NAME)
    with open(os.path.join(share, 'urdf', BASE_URDF), 'r', encoding='utf-8') as urdf:
        text = urdf.read()
    controllers = os.path.join(share, 'config', 'controllers_nav.yaml')
    return build_robot_description(text, controllers, sim)
