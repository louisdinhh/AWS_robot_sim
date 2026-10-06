#!/usr/bin/env python3
"""Send a single linear/angular velocity command to the UGV for a set duration.

Usage:
  ros2 run ugv_robot send_velocity.py --linear 0.3 --angular 0.0 --duration 2.0
"""
import argparse
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class VelocitySender(Node):
    def __init__(self, linear: float, angular: float, duration: float, topic: str):
        super().__init__('send_velocity')
        self.pub = self.create_publisher(Twist, topic, 10)
        self.linear = linear
        self.angular = angular
        self.duration = duration

    def run(self):
        msg = Twist()
        msg.linear.x = self.linear
        msg.angular.z = self.angular

        rate_hz = 10.0
        end_time = time.time() + self.duration
        self.get_logger().info(
            f'Sending linear.x={self.linear}, angular.z={self.angular} for {self.duration}s')
        while time.time() < end_time:
            self.pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=1.0 / rate_hz)

        # Always stop the robot at the end.
        stop = Twist()
        self.pub.publish(stop)
        self.get_logger().info('Done — stopped the robot.')


def main():
    parser = argparse.ArgumentParser(description='Send a velocity command to /cmd_vel.')
    parser.add_argument('--linear', type=float, default=0.0, help='Linear x velocity (m/s)')
    parser.add_argument('--angular', type=float, default=0.0, help='Angular z velocity (rad/s)')
    parser.add_argument('--duration', type=float, default=2.0, help='How long to send the command (s)')
    parser.add_argument('--topic', type=str, default='/cmd_vel', help='Topic to publish to')
    args, _ = parser.parse_known_args()

    rclpy.init()
    node = VelocitySender(args.linear, args.angular, args.duration, args.topic)
    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
