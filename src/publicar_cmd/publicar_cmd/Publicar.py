import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist


class PublicarCMD(Node):

    def __init__(self):
        super().__init__('publicar_vel')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        timer_period = 0.01  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)


    def timer_callback(self):
        msg=Twist()
        msg.linear.x = 0.1
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg)



def main(args=None):
    rclpy.init(args=args)

    publicar_vel = PublicarCMD()

    rclpy.spin(publicar_vel)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    publicar_vel.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()