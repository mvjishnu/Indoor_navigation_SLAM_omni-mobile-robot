"""Convert geometry_msgs/Twist into TwistStamped for the mecanum controller."""

from geometry_msgs.msg import Twist, TwistStamped
import rclpy
from rclpy.node import Node


class CmdVelStamper(Node):
    """Republish Nav2 / teleop Twist commands as TwistStamped."""

    def __init__(self):
        """Create the subscriber and publisher."""
        super().__init__('cmd_vel_stamper')
        self.declare_parameter('input_topic', '/cmd_vel')
        self.declare_parameter('output_topic', '/mecanum_drive_controller/reference')
        self.declare_parameter('frame_id', 'base_footprint')
        self._frame_id = self.get_parameter('frame_id').value
        self._pub = self.create_publisher(
            TwistStamped, self.get_parameter('output_topic').value, 10)
        self.create_subscription(
            Twist, self.get_parameter('input_topic').value, self._on_twist, 10)

    def _on_twist(self, msg):
        out = TwistStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self._frame_id
        out.twist = msg
        self._pub.publish(out)


def main(args=None):
    """Run the node."""
    rclpy.init(args=args)
    node = CmdVelStamper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
