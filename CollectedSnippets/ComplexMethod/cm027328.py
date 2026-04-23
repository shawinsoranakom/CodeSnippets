def _setup_from_config(self, config: ConfigType) -> None:
        """(Re)Setup the entity."""
        self._attr_operation_list = config[CONF_MODE_LIST]
        self._attr_temperature_unit = config.get(
            CONF_TEMPERATURE_UNIT, self.hass.config.units.temperature_unit
        )
        if (min_temp := config.get(CONF_TEMP_MIN)) is not None:
            self._attr_min_temp = min_temp
        if (max_temp := config.get(CONF_TEMP_MAX)) is not None:
            self._attr_max_temp = max_temp
        if (precision := config.get(CONF_PRECISION)) is not None:
            self._attr_precision = precision

        self._topic = {key: config.get(key) for key in TOPIC_KEYS}

        self._optimistic = config[CONF_OPTIMISTIC]

        # Set init temp, if it is missing convert the default to the temperature units
        init_temp: float = config.get(
            CONF_TEMP_INITIAL,
            TemperatureConverter.convert(
                DEFAULT_MIN_TEMP,
                UnitOfTemperature.FAHRENHEIT,
                self.temperature_unit,
            ),
        )
        if self._topic[CONF_TEMP_STATE_TOPIC] is None or self._optimistic:
            self._attr_target_temperature = init_temp
        if self._topic[CONF_MODE_STATE_TOPIC] is None or self._optimistic:
            self._attr_current_operation = STATE_OFF

        value_templates: dict[str, Template | None] = {
            key: config.get(CONF_VALUE_TEMPLATE) for key in VALUE_TEMPLATE_KEYS
        }
        value_templates.update(
            {key: config[key] for key in VALUE_TEMPLATE_KEYS & config.keys()}
        )
        self._value_templates = {
            key: MqttValueTemplate(
                template, entity=self
            ).async_render_with_possible_json_value
            for key, template in value_templates.items()
        }

        self._command_templates = {
            key: MqttCommandTemplate(config.get(key), entity=self).async_render
            for key in COMMAND_TEMPLATE_KEYS
        }

        support = WaterHeaterEntityFeature(0)
        if (self._topic[CONF_TEMP_STATE_TOPIC] is not None) or (
            self._topic[CONF_TEMP_COMMAND_TOPIC] is not None
        ):
            support |= WaterHeaterEntityFeature.TARGET_TEMPERATURE

        if (self._topic[CONF_MODE_STATE_TOPIC] is not None) or (
            self._topic[CONF_MODE_COMMAND_TOPIC] is not None
        ):
            support |= WaterHeaterEntityFeature.OPERATION_MODE

        if self._topic[CONF_POWER_COMMAND_TOPIC] is not None:
            support |= WaterHeaterEntityFeature.ON_OFF

        self._attr_supported_features = support