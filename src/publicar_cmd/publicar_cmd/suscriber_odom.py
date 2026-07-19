import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry


class OdomSuscriber(Node):

    def __init__(self):
        super().__init__('odom_suscriber')
        self.subscription = self.create_subscription(
            Odometry,
            '/wheel/odometry',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info('I heard: "%s"' % msg.twist.twist.linear)


def main(args=None):
    rclpy.init(args=args)

    odom_suscriber = OdomSuscriber()

    rclpy.spin(odom_suscriber)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    odom_suscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()