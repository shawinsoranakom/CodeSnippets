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

        self._topics = {
            key: config.get(key) for key in (CONF_STATE_TOPIC, CONF_COMMAND_TOPIC)
        }
        self._command_templates = {
            key: MqttCommandTemplate(config[key], entity=self).async_render
            for key in COMMAND_TEMPLATES
        }
        self._value_templates = {
            key: MqttValueTemplate(
                config.get(key), entity=self
            ).async_render_with_possible_json_value
            for key in VALUE_TEMPLATES
        }
        optimistic: bool = config[CONF_OPTIMISTIC]
        self._optimistic = (
            optimistic
            or self._topics[CONF_STATE_TOPIC] is None
            or CONF_STATE_TEMPLATE not in self._config
        )
        self._attr_assumed_state = bool(self._optimistic)

        color_modes = {ColorMode.ONOFF}
        if CONF_BRIGHTNESS_TEMPLATE in config:
            color_modes.add(ColorMode.BRIGHTNESS)
        if CONF_COLOR_TEMP_TEMPLATE in config:
            color_modes.add(ColorMode.COLOR_TEMP)
        if (
            CONF_RED_TEMPLATE in config
            and CONF_GREEN_TEMPLATE in config
            and CONF_BLUE_TEMPLATE in config
        ):
            color_modes.add(ColorMode.HS)
        self._attr_supported_color_modes = filter_supported_color_modes(color_modes)
        self._fixed_color_mode = None
        self._attr_color_mode = ColorMode.UNKNOWN
        if self.supported_color_modes and len(self.supported_color_modes) == 1:
            self._fixed_color_mode = next(iter(self.supported_color_modes))
            self._attr_color_mode = self._fixed_color_mode

        features = LightEntityFeature.FLASH | LightEntityFeature.TRANSITION
        if config.get(CONF_EFFECT_LIST) is not None:
            features = features | LightEntityFeature.EFFECT
        self._attr_supported_features = features