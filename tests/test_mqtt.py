"""Tests for MQTT client and simulated publishing."""

from app.mqtt import MQTTClient


def test_mqtt_publish_and_subscribe():
    client = MQTTClient(host="invalid-broker", port=9999)
    # Even when offline, client handles publishing gracefully without throwing errors
    success = client.publish("test/topic", {"status": "ok"})
    assert success is True

    # Subscription callback registration
    received = []

    def on_msg(topic, payload):
        received.append((topic, payload))

    client.subscribe("frigate/events", on_msg)
    assert "frigate/events" in client._callbacks

    # Test callback invocation
    client._callbacks["frigate/events"][0]("frigate/events", {"event": "person"})
    assert len(received) == 1
    assert received[0][1]["event"] == "person"
    client.stop()
