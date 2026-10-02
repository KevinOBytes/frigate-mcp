"""MQTT integration for Frigate-MCP.

Handles real-time MQTT message publishing and subscriptions for Frigate NVR
camera events, motion triggers, and sensor notifications.
"""

import json
import logging
import os
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("frigate-mcp.mqtt")


class MQTTClient:
    """MQTT client for Frigate ecosystem communication."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        topic_prefix: str = "frigate",
    ):
        self.host = host or os.getenv("MQTT_HOST", os.getenv("FRIGATE_MQTT_HOST", "localhost"))
        self.port = port or int(os.getenv("MQTT_PORT", os.getenv("FRIGATE_MQTT_PORT", "1883")))
        self.username = username or os.getenv("MQTT_USER")
        self.password = password or os.getenv("MQTT_PASSWORD")
        self.topic_prefix = topic_prefix.rstrip("/")
        self.is_connected = False
        self._client = None
        self._callbacks: Dict[str, List[Callable[[str, Any], None]]] = {}
        self._init_client()

    def _init_client(self) -> None:
        """Initialize paho-mqtt client if available."""
        try:
            import paho.mqtt.client as mqtt

            # Support paho-mqtt v2 CallbackAPIVersion
            try:
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            except AttributeError:
                client = mqtt.Client()

            if self.username and self.password:
                client.username_pw_set(self.username, self.password)

            client.on_connect = self._on_connect
            client.on_message = self._on_message
            self._client = client

            # Attempt non-blocking connection
            client.connect_async(self.host, self.port, 60)
            client.loop_start()
            logger.info("Connecting to MQTT broker at %s:%s", self.host, self.port)
        except Exception as e:
            self._client = None
            self.is_connected = False
            logger.debug("MQTT broker not available at %s:%s (running simulated MQTT): %s", self.host, self.port, e)

    def _on_connect(self, client, userdata, flags, rc, properties=None) -> None:
        """Callback on broker connection."""
        if rc == 0:
            self.is_connected = True
            logger.info("Connected to MQTT broker at %s:%s", self.host, self.port)
            # Subscribe to frigate events and status
            client.subscribe(f"{self.topic_prefix}/events")
            client.subscribe(f"{self.topic_prefix}/+/motion")
            client.subscribe(f"{self.topic_prefix}/available")
        else:
            self.is_connected = False
            logger.warning("Failed to connect to MQTT broker, return code %s", rc)

    def _on_message(self, client, userdata, msg) -> None:
        """Callback on message received."""
        topic = msg.topic
        payload_str = msg.payload.decode("utf-8", errors="replace")
        try:
            payload = json.loads(payload_str)
        except Exception:
            payload = payload_str

        for registered_topic, callbacks in self._callbacks.items():
            if registered_topic == topic or registered_topic == "#":
                for cb in callbacks:
                    try:
                        cb(topic, payload)
                    except Exception as e:
                        logger.error("Error in MQTT callback for %s: %s", topic, e)

    def publish(self, topic_suffix: str, payload: Any) -> bool:
        """Publish message under frigate topic prefix."""
        full_topic = f"{self.topic_prefix}/{topic_suffix.lstrip('/')}"
        msg = json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload)

        if self.is_connected and self._client:
            try:
                self._client.publish(full_topic, msg)
                return True
            except Exception as e:
                logger.warning("MQTT publish failed for %s: %s", full_topic, e)

        logger.debug("Simulated MQTT publish to %s: %s", full_topic, msg)
        return True

    def subscribe(self, topic: str, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for a specific topic."""
        if topic not in self._callbacks:
            self._callbacks[topic] = []
        self._callbacks[topic].append(callback)
        if self.is_connected and self._client:
            try:
                self._client.subscribe(topic)
            except Exception as e:
                logger.warning("Failed to subscribe to MQTT topic %s: %s", topic, e)

    def stop(self) -> None:
        """Stop MQTT loop and disconnect."""
        if self._client:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass


_mqtt_instance: Optional[MQTTClient] = None


def get_mqtt() -> MQTTClient:
    """Retrieve singleton MQTTClient instance."""
    global _mqtt_instance
    if _mqtt_instance is None:
        _mqtt_instance = MQTTClient()
    return _mqtt_instance


def reset_mqtt() -> MQTTClient:
    """Reset singleton MQTTClient instance."""
    global _mqtt_instance
    if _mqtt_instance:
        _mqtt_instance.stop()
    _mqtt_instance = MQTTClient()
    return _mqtt_instance
