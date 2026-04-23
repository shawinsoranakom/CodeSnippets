def _setup_from_config(self, config: ConfigType) -> None:
        """(Re)Setup the entity."""
        self._color_temp_kelvin = config[CONF_COLOR_TEMP_KELVIN]
        self._attr_min_color_temp_kelvin = (
            color_util.color_temperature_mired_to_kelvin(max_mireds)
            if (max_mireds := config.get(CONF_MAX_MIREDS))
            else config.get(CONF_MIN_KELVIN, DEFAULT_MIN_KELVIN)
        )
        self._attr_max_color_temp_kelvin = (
            color_util.color_temperature_mired_to_kelvin(min_mireds)
            if (min_mireds := config.get(CONF_MIN_MIREDS))
            else config.get(CONF_MAX_KELVIN, DEFAULT_MAX_KELVIN)
        )

        self._attr_effect_list = config.get(CONF_EFFECT_LIST)

        topic: dict[str, str | None] = {
            key: config.get(key)
            for key in (
                CONF_BRIGHTNESS_COMMAND_TOPIC,
                CONF_BRIGHTNESS_STATE_TOPIC,
                CONF_COLOR_MODE_STATE_TOPIC,
                CONF_COLOR_TEMP_COMMAND_TOPIC,
                CONF_COLOR_TEMP_STATE_TOPIC,
                CONF_COMMAND_TOPIC,
                CONF_EFFECT_COMMAND_TOPIC,
                CONF_EFFECT_STATE_TOPIC,
                CONF_HS_COMMAND_TOPIC,
                CONF_HS_STATE_TOPIC,
                CONF_RGB_COMMAND_TOPIC,
                CONF_RGB_STATE_TOPIC,
                CONF_RGBW_COMMAND_TOPIC,
                CONF_RGBW_STATE_TOPIC,
                CONF_RGBWW_COMMAND_TOPIC,
                CONF_RGBWW_STATE_TOPIC,
                CONF_STATE_TOPIC,
                CONF_WHITE_COMMAND_TOPIC,
                CONF_XY_COMMAND_TOPIC,
                CONF_XY_STATE_TOPIC,
            )
        }
        self._topic = topic
        self._payload = {"on": config[CONF_PAYLOAD_ON], "off": config[CONF_PAYLOAD_OFF]}

        self._value_templates = {
            key: MqttValueTemplate(
                config.get(key), entity=self
            ).async_render_with_possible_json_value
            for key in VALUE_TEMPLATE_KEYS
        }

        self._command_templates = {
            key: MqttCommandTemplate(config.get(key), entity=self).async_render
            for key in COMMAND_TEMPLATE_KEYS
        }

        optimistic: bool = config[CONF_OPTIMISTIC]
        self._optimistic_color_mode = (
            optimistic or topic[CONF_COLOR_MODE_STATE_TOPIC] is None
        )
        self._optimistic = optimistic or topic[CONF_STATE_TOPIC] is None
        self._attr_assumed_state = bool(self._optimistic)
        self._optimistic_rgb_color = optimistic or topic[CONF_RGB_STATE_TOPIC] is None
        self._optimistic_rgbw_color = optimistic or topic[CONF_RGBW_STATE_TOPIC] is None
        self._optimistic_rgbww_color = (
            optimistic or topic[CONF_RGBWW_STATE_TOPIC] is None
        )
        self._optimistic_brightness = (
            optimistic
            or (
                topic[CONF_BRIGHTNESS_COMMAND_TOPIC] is not None
                and topic[CONF_BRIGHTNESS_STATE_TOPIC] is None
            )
            or (
                topic[CONF_BRIGHTNESS_COMMAND_TOPIC] is None
                and topic[CONF_RGB_STATE_TOPIC] is None
            )
        )
        self._optimistic_color_temp_kelvin = (
            optimistic or topic[CONF_COLOR_TEMP_STATE_TOPIC] is None
        )
        self._optimistic_effect = optimistic or topic[CONF_EFFECT_STATE_TOPIC] is None
        self._optimistic_hs_color = optimistic or topic[CONF_HS_STATE_TOPIC] is None
        self._optimistic_xy_color = optimistic or topic[CONF_XY_STATE_TOPIC] is None
        supported_color_modes: set[ColorMode] = set()
        if topic[CONF_COLOR_TEMP_COMMAND_TOPIC] is not None:
            supported_color_modes.add(ColorMode.COLOR_TEMP)
            self._attr_color_mode = ColorMode.COLOR_TEMP
        if topic[CONF_HS_COMMAND_TOPIC] is not None:
            supported_color_modes.add(ColorMode.HS)
            self._attr_color_mode = ColorMode.HS
        if topic[CONF_RGB_COMMAND_TOPIC] is not None:
            supported_color_modes.add(ColorMode.RGB)
            self._attr_color_mode = ColorMode.RGB
        if topic[CONF_RGBW_COMMAND_TOPIC] is not None:
            supported_color_modes.add(ColorMode.RGBW)
            self._attr_color_mode = ColorMode.RGBW
        if topic[CONF_RGBWW_COMMAND_TOPIC] is not None:
            supported_color_modes.add(ColorMode.RGBWW)
            self._attr_color_mode = ColorMode.RGBWW
        if topic[CONF_WHITE_COMMAND_TOPIC] is not None:
            supported_color_modes.add(ColorMode.WHITE)
        if topic[CONF_XY_COMMAND_TOPIC] is not None:
            supported_color_modes.add(ColorMode.XY)
            self._attr_color_mode = ColorMode.XY
        if len(supported_color_modes) > 1:
            self._attr_color_mode = ColorMode.UNKNOWN

        if not supported_color_modes:
            if topic[CONF_BRIGHTNESS_COMMAND_TOPIC] is not None:
                self._attr_color_mode = ColorMode.BRIGHTNESS
                supported_color_modes.add(ColorMode.BRIGHTNESS)
            else:
                self._attr_color_mode = ColorMode.ONOFF
                supported_color_modes.add(ColorMode.ONOFF)

        # Validate the color_modes configuration
        self._attr_supported_color_modes = valid_supported_color_modes(
            supported_color_modes
        )

        self._attr_supported_features = LightEntityFeature(0)
        if topic[CONF_EFFECT_COMMAND_TOPIC] is not None:
            self._attr_supported_features |= LightEntityFeature.EFFECT