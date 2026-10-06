import os
import time

from awscrt import mqtt
from awsiot import mqtt_connection_builder


ENDPOINT = os.environ["AWS_IOT_ENDPOINT"]

CERT = os.path.expanduser(
    "~/ugv_ws/src/ugv_robot/certs/eeb0e82128759314041167c0059b410e6a6d4dc7112a36e77df73a3d16d4c08c-certificate.pem.crt"
)

PRIVATE_KEY = os.path.expanduser(
    "~/ugv_ws/src/ugv_robot/certs/eeb0e82128759314041167c0059b410e6a6d4dc7112a36e77df73a3d16d4c08c-private.pem.key"
)

CA = os.path.expanduser(
    "~/ugv_ws/src/ugv_robot/certs/AmazonRootCA1.pem"
)

CLIENT_ID = "UGV-Simulation"
TOPIC = "ugv/test"


def on_message_received(topic, payload, **kwargs):
    print(
        f"Received message:\n"
        f"  topic: {topic}\n"
        f"  payload: {payload.decode()}"
    )


mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=CERT,
    pri_key_filepath=PRIVATE_KEY,
    ca_filepath=CA,
    client_id=CLIENT_ID,
    clean_session=True,
    keep_alive_secs=30
)

print("Connecting to AWS IoT...")

mqtt_connection.connect().result()

print("Connected!")

subscribe_future, packet_id = mqtt_connection.subscribe(
    topic=TOPIC,
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=on_message_received
)

subscribe_future.result()

print(f"Subscribed to {TOPIC}")
print("Waiting for messages...")

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Disconnecting...")

finally:
    mqtt_connection.disconnect().result()