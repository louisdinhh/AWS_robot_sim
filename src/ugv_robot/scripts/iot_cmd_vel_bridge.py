#!/usr/bin/env python3

import json
import os
import threading

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from awscrt import mqtt
from awsiot import mqtt_connection_builder


class IoTCmdVelBridge(Node):

    def __init__(self):
        super().__init__('iot_cmd_vel_bridge')

        # ==================================================
        # AWS IoT configuration
        # ==================================================

        self.endpoint = os.environ.get('AWS_IOT_ENDPOINT')

        if not self.endpoint:
            raise RuntimeError(
                'AWS_IOT_ENDPOINT environment variable is not set'
            )

        self.cert_dir = os.path.expanduser(
            '~/ugv_ws/src/ugv_robot/certs'
        )

        self.cert_file = os.path.join(
            self.cert_dir,
            'eeb0e82128759314041167c0059b410e6a6d4dc7112a36e77df73a3d16d4c08c-certificate.pem.crt'
        )

        self.private_key = os.path.join(
            self.cert_dir,
            'eeb0e82128759314041167c0059b410e6a6d4dc7112a36e77df73a3d16d4c08c-private.pem.key'
        )

        self.ca_file = os.path.join(
            self.cert_dir,
            'AmazonRootCA1.pem'
        )

        self.mqtt_topic = 'ugv/cmd_vel'

        # ==================================================
        # ROS publisher
        # ==================================================

        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # ==================================================
        # Safety limits
        # ==================================================

        self.max_linear = 1.0
        self.max_angular = 1.5

        self.stop_timer = None

        # ==================================================
        # Connect to AWS IoT
        # ==================================================

        self.get_logger().info(
            f'Connecting to AWS IoT: {self.endpoint}'
        )

        self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.endpoint,
            cert_filepath=self.cert_file,
            pri_key_filepath=self.private_key,
            ca_filepath=self.ca_file,
            client_id='UGV-Simulation',
            clean_session=True,
            keep_alive_secs=30
        )

        self.mqtt_connection.connect().result()

        self.get_logger().info(
            'Connected to AWS IoT Core'
        )

        # ==================================================
        # Subscribe
        # ==================================================

        subscribe_future, packet_id = self.mqtt_connection.subscribe(
            topic=self.mqtt_topic,
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=self.on_mqtt_message
        )

        subscribe_future.result()

        self.get_logger().info(
            f'Subscribed to {self.mqtt_topic}'
        )

    # ======================================================
    # MQTT callback
    # ======================================================

    def on_mqtt_message(
        self,
        topic,
        payload,
        **kwargs
    ):
        try:

            data = json.loads(
                payload.decode('utf-8')
            )

            self.get_logger().info(
                f'Received MQTT command: {data}'
            )

            linear = float(
                data.get('linear', 0.0)
            )

            angular = float(
                data.get('angular', 0.0)
            )

            duration = float(
                data.get('duration', 0.0)
            )

            # ==================================================
            # Safety limits
            # ==================================================

            linear = max(
                -self.max_linear,
                min(self.max_linear, linear)
            )

            angular = max(
                -self.max_angular,
                min(self.max_angular, angular)
            )

            # ==================================================
            # Publish Twist
            # ==================================================

            msg = Twist()

            msg.linear.x = linear
            msg.angular.z = angular

            self.cmd_vel_pub.publish(msg)

            self.get_logger().info(
                f'Published /cmd_vel: '
                f'linear.x={linear:.2f}, '
                f'angular.z={angular:.2f}'
            )

            # ==================================================
            # Stop after duration
            # ==================================================

            if duration > 0:

                if self.stop_timer is not None:
                    self.stop_timer.cancel()

                self.stop_timer = threading.Timer(
                    duration,
                    self.stop_robot
                )

                self.stop_timer.start()

        except Exception as e:

            self.get_logger().error(
                f'Failed to process MQTT command: {e}'
            )

    # ======================================================
    # Stop robot
    # ======================================================

    def stop_robot(self):

        msg = Twist()

        self.cmd_vel_pub.publish(msg)

        self.get_logger().info(
            'Robot stopped'
        )


def main(args=None):

    rclpy.init(args=args)

    node = None

    try:

        node = IoTCmdVelBridge()

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        if node is not None:

            # Always stop robot
            node.stop_robot()

            try:
                node.mqtt_connection.disconnect().result()
            except Exception:
                pass

            node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':
    main()