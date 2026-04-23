def _rgbx_received(
        self,
        msg: ReceiveMessage,
        template: str,
        color_mode: ColorMode,
        convert_color: Callable[..., tuple[int, ...]],
    ) -> tuple[int, ...] | None:
        """Process MQTT messages for RGBW and RGBWW."""
        payload = self._value_templates[template](msg.payload, PayloadSentinel.DEFAULT)
        if payload is PayloadSentinel.DEFAULT or not payload:
            _LOGGER.debug("Ignoring empty %s message from '%s'", color_mode, msg.topic)
            return None
        color = tuple(int(val) for val in str(payload).split(","))
        if self._optimistic_color_mode:
            self._attr_color_mode = color_mode
        if self._topic[CONF_BRIGHTNESS_STATE_TOPIC] is None:
            rgb = convert_color(*color)
            brightness = max(rgb)
            if brightness == 0:
                _LOGGER.debug(
                    "Ignoring %s message with zero rgb brightness from '%s'",
                    color_mode,
                    msg.topic,
                )
                return None
            self._attr_brightness = brightness
            # Normalize the color to 100% brightness
            color = tuple(
                min(round(channel / brightness * 255), 255) for channel in color
            )
        return color