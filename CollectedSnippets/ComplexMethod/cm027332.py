def _state_received(self, msg: ReceiveMessage) -> None:
        """Handle new MQTT messages."""
        state_value = self._value_templates[CONF_STATE_TEMPLATE](
            msg.payload,
            PayloadSentinel.NONE,
        )
        if not state_value:
            _LOGGER.debug(
                "Ignoring message from '%s' with empty state value", msg.topic
            )
        elif state_value == STATE_ON:
            self._attr_is_on = True
        elif state_value == STATE_OFF:
            self._attr_is_on = False
        elif state_value == PAYLOAD_NONE:
            self._attr_is_on = None
        else:
            _LOGGER.warning(
                "Invalid state value '%s' received from %s",
                state_value,
                msg.topic,
            )

        if CONF_BRIGHTNESS_TEMPLATE in self._config:
            brightness_value = self._value_templates[CONF_BRIGHTNESS_TEMPLATE](
                msg.payload,
                PayloadSentinel.NONE,
            )
            if not brightness_value:
                _LOGGER.debug(
                    "Ignoring message from '%s' with empty brightness value",
                    msg.topic,
                )
            else:
                try:
                    if brightness := int(brightness_value):
                        self._attr_brightness = brightness
                    else:
                        _LOGGER.debug(
                            "Ignoring zero brightness value for entity %s",
                            self.entity_id,
                        )
                except ValueError:
                    _LOGGER.warning(
                        "Invalid brightness value '%s' received from %s",
                        brightness_value,
                        msg.topic,
                    )

        if CONF_COLOR_TEMP_TEMPLATE in self._config:
            color_temp_value = self._value_templates[CONF_COLOR_TEMP_TEMPLATE](
                msg.payload,
                PayloadSentinel.NONE,
            )
            if not color_temp_value:
                _LOGGER.debug(
                    "Ignoring message from '%s' with empty color temperature value",
                    msg.topic,
                )
            else:
                try:
                    self._attr_color_temp_kelvin = (
                        int(color_temp_value)
                        if self._color_temp_kelvin
                        else color_util.color_temperature_mired_to_kelvin(
                            int(color_temp_value)
                        )
                        if color_temp_value != "None"
                        else None
                    )
                    self._update_color_mode()
                except ValueError:
                    _LOGGER.warning(
                        "Invalid color temperature value '%s' received from %s",
                        color_temp_value,
                        msg.topic,
                    )

        if (
            CONF_RED_TEMPLATE in self._config
            and CONF_GREEN_TEMPLATE in self._config
            and CONF_BLUE_TEMPLATE in self._config
        ):
            red_value = self._value_templates[CONF_RED_TEMPLATE](
                msg.payload,
                PayloadSentinel.NONE,
            )
            green_value = self._value_templates[CONF_GREEN_TEMPLATE](
                msg.payload,
                PayloadSentinel.NONE,
            )
            blue_value = self._value_templates[CONF_BLUE_TEMPLATE](
                msg.payload,
                PayloadSentinel.NONE,
            )
            if not red_value or not green_value or not blue_value:
                _LOGGER.debug(
                    "Ignoring message from '%s' with empty color value", msg.topic
                )
            elif red_value == "None" and green_value == "None" and blue_value == "None":
                self._attr_hs_color = None
                self._update_color_mode()
            else:
                try:
                    self._attr_hs_color = color_util.color_RGB_to_hs(
                        int(red_value), int(green_value), int(blue_value)
                    )
                    self._update_color_mode()
                except ValueError:
                    _LOGGER.warning("Invalid color value received from %s", msg.topic)

        if CONF_EFFECT_TEMPLATE in self._config:
            effect_value = self._value_templates[CONF_EFFECT_TEMPLATE](
                msg.payload,
                PayloadSentinel.NONE,
            )
            if not effect_value:
                _LOGGER.debug(
                    "Ignoring message from '%s' with empty effect value", msg.topic
                )
            elif (effect_list := self._config[CONF_EFFECT_LIST]) and str(
                effect_value
            ) in effect_list:
                self._attr_effect = str(effect_value)
            else:
                _LOGGER.warning(
                    "Unsupported effect value '%s' received from %s",
                    effect_value,
                    msg.topic,
                )