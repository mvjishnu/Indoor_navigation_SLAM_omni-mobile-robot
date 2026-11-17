"""
Assemble the robot_description used by the SLAM and navigation launch files.

The original ``urdf/omni_mobile_bot.urdf`` is never modified.  Two things are
appended to it at launch time:

* a ``base_footprint`` frame that sits at the geometric centre of the four
  wheels with x pointing to the front of the robot (the camera side).  The
  mecanum controller and the EKF both assume that convention, whereas the CAD
  ``base_link`` is on a wheel corner with +y pointing forward.
* (simulation only) the Gazebo lidar, IMU and camera sensors, modelled on the
  RPLiDAR C1 and the MPU9250 so that the simulation resembles the real parts.
  The camera is for viewing only (``/camera/image_raw``); navigation does not
  use it.
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

# Forward-looking view camera on camera_link. camera_link is rotated -90 deg
# about x in the URDF; this sensor pose turns the optical axis (sensor +x) to
# the robot's forward direction (base_link +y) with the image upright.
CAMERA_RPY = '-3.141593 -1.570796 -1.570796'
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 360
CAMERA_RATE_HZ = 15
CAMERA_HFOV = 1.2   # rad (~69 deg)

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

  <gazebo reference="camera_link">
    <sensor name="view_camera" type="camera">
      <pose>0 0 0 {CAMERA_RPY}</pose>
      <topic>camera/image_raw</topic>
      <gz_frame_id>camera_link</gz_frame_id>
      <update_rate>{CAMERA_RATE_HZ}</update_rate>
      <always_on>true</always_on>
      <visualize>false</visualize>
      <camera>
        <camera_info_topic>camera/camera_info</camera_info_topic>
        <horizontal_fov>{CAMERA_HFOV}</horizontal_fov>
        <image>
          <width>{CAMERA_WIDTH}</width>
          <height>{CAMERA_HEIGHT}</height>
          <format>R8G8B8</format>
        </image>
        <clip>
          <near>0.05</near>
          <far>30.0</far>
        </clip>
      </camera>
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


ROLLER_JOINT_RE = re.compile(
    r'<joint\s+name="([^"]*roller[^"]*)"\s+type="continuous"')

# Gazebo topic carrying the passive roller joint states (bridged to /joint_states).
ROLLER_STATE_TOPIC = 'roller_joint_states'


def roller_joint_names(urdf_text):
    """Names of the free-spinning mecanum roller joints in the URDF."""
    return ROLLER_JOINT_RE.findall(urdf_text)


def _roller_state_xml(joints):
    """
    Gazebo JointStatePublisher for the passive rollers.

    ros2_control only reports the four driven wheel joints, so without this
    robot_state_publisher never gets roller joint states, the roller frames
    never appear in TF, and RViz cannot draw the rollers.
    """
    names = ''.join(f'\n      <joint_name>{j}</joint_name>' for j in joints)
    return f"""
  <!-- ===== roller joint states for RViz (added by mecanum_bot.robot_description) ===== -->
  <gazebo>
    <plugin filename="gz-sim-joint-state-publisher-system"
            name="gz::sim::systems::JointStatePublisher">
      <topic>{ROLLER_STATE_TOPIC}</topic>{names}
    </plugin>
  </gazebo>
"""


def build_robot_description(urdf_text, controllers_yaml=None, sim=True):
    """
    Return the URDF string with the navigation additions applied.

    ``controllers_yaml`` replaces the ros2_control parameter file that the
    original URDF hard-codes (simulation only).

    On real hardware nothing measures the passive rollers, so their joints are
    turned into fixed joints; robot_state_publisher then publishes them as
    static frames and RViz still draws them.
    """
    extra = NAV_FRAMES_XML
    rollers = roller_joint_names(urdf_text)
    if not sim:
        urdf_text = ROLLER_JOINT_RE.sub(
            lambda m: m.group(0).replace('continuous', 'fixed'), urdf_text)
    if sim:
        extra += _roller_state_xml(rollers)
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
