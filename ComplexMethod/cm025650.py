def handle_event(self, event: dict) -> None:
        """Handle webhook events."""
        data = event["data"]
        event_type = data.get(ATTR_EVENT_TYPE)
        push_type = data.get(WEBHOOK_PUSH_TYPE)

        if not push_type:
            _LOGGER.debug("Event has no push_type, returning")
            return

        if not data.get("camera_id"):
            _LOGGER.debug("Event %s has no camera ID, returning", event_type)
            return

        if (
            data["home_id"] == self.home.entity_id
            and data["camera_id"] == self.device.entity_id
        ):
            # device_type to be stripped "DeviceType."
            device_push_type = f"{self.device_type.name}-{event_type}"
            if push_type != device_push_type:
                _LOGGER.debug(
                    "Event push_type %s does not match device push_type %s, returning",
                    push_type,
                    device_push_type,
                )
                return

            if event_type in [EVENT_TYPE_DISCONNECTION, EVENT_TYPE_OFF]:
                _LOGGER.debug(
                    "Camera %s has received %s event, turning off and idleing streaming",
                    data["camera_id"],
                    event_type,
                )
                self._attr_is_streaming = False
                self._monitoring = False
            elif event_type in [EVENT_TYPE_CONNECTION, EVENT_TYPE_ON]:
                _LOGGER.debug(
                    "Camera %s has received %s event, turning on and enabling streaming if applicable",
                    data["camera_id"],
                    event_type,
                )
                if self.device_type != "NDB":
                    self._attr_is_streaming = True
                self._monitoring = True
            elif event_type == EVENT_TYPE_LIGHT_MODE:
                if data.get("sub_type"):
                    self._light_state = data["sub_type"]
                else:
                    _LOGGER.debug(
                        "Camera %s has received light mode event without sub_type",
                        data["camera_id"],
                    )
            else:
                _LOGGER.debug(
                    "Camera %s has received unexpected event as type %s",
                    data["camera_id"],
                    event_type,
                )

            self.async_write_ha_state()
            return