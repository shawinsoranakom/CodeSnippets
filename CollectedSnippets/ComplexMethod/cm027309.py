def _setup_from_config(self, config: ConfigType) -> None:
        """(Re)Setup the entity."""
        self._attr_device_class = config.get(CONF_DEVICE_CLASS)
        self._attr_min_humidity = config[CONF_TARGET_HUMIDITY_MIN]
        self._attr_max_humidity = config[CONF_TARGET_HUMIDITY_MAX]

        self._topic = {key: config.get(key) for key in TOPICS}
        self._payload = {
            "STATE_ON": config[CONF_PAYLOAD_ON],
            "STATE_OFF": config[CONF_PAYLOAD_OFF],
            "HUMIDITY_RESET": config[CONF_PAYLOAD_RESET_HUMIDITY],
            "MODE_RESET": config[CONF_PAYLOAD_RESET_MODE],
        }
        if CONF_MODE_COMMAND_TOPIC in config and CONF_AVAILABLE_MODES_LIST in config:
            self._attr_available_modes = config[CONF_AVAILABLE_MODES_LIST]
        else:
            self._attr_available_modes = []
        if self._attr_available_modes:
            self._attr_supported_features = HumidifierEntityFeature.MODES
        if CONF_MODE_STATE_TOPIC in config:
            self._attr_mode = None

        optimistic: bool = config[CONF_OPTIMISTIC]
        self._optimistic = optimistic or self._topic[CONF_STATE_TOPIC] is None
        self._attr_assumed_state = bool(self._optimistic)
        self._optimistic_target_humidity = (
            optimistic or self._topic[CONF_TARGET_HUMIDITY_STATE_TOPIC] is None
        )
        self._optimistic_mode = optimistic or self._topic[CONF_MODE_STATE_TOPIC] is None

        command_templates: dict[str, Template | None] = {
            CONF_STATE: config.get(CONF_COMMAND_TEMPLATE),
            ATTR_HUMIDITY: config.get(CONF_TARGET_HUMIDITY_COMMAND_TEMPLATE),
            ATTR_MODE: config.get(CONF_MODE_COMMAND_TEMPLATE),
        }
        self._command_templates = {
            key: MqttCommandTemplate(tpl, entity=self).async_render
            for key, tpl in command_templates.items()
        }

        value_templates: dict[str, Template | None] = {
            ATTR_ACTION: config.get(CONF_ACTION_TEMPLATE),
            ATTR_CURRENT_HUMIDITY: config.get(CONF_CURRENT_HUMIDITY_TEMPLATE),
            CONF_STATE: config.get(CONF_STATE_VALUE_TEMPLATE),
            ATTR_HUMIDITY: config.get(CONF_TARGET_HUMIDITY_STATE_TEMPLATE),
            ATTR_MODE: config.get(CONF_MODE_STATE_TEMPLATE),
        }
        self._value_templates = {
            key: MqttValueTemplate(
                tpl,
                entity=self,
            ).async_render_with_possible_json_value
            for key, tpl in value_templates.items()
        }