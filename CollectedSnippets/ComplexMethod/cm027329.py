def _setup_from_config(self, config: ConfigType) -> None:
        """(Re)Setup the entity."""
        self._speed_range = (
            config[CONF_SPEED_RANGE_MIN],
            config[CONF_SPEED_RANGE_MAX],
        )
        self._topic = {
            key: config.get(key)
            for key in (
                CONF_STATE_TOPIC,
                CONF_COMMAND_TOPIC,
                CONF_DIRECTION_STATE_TOPIC,
                CONF_DIRECTION_COMMAND_TOPIC,
                CONF_PERCENTAGE_STATE_TOPIC,
                CONF_PERCENTAGE_COMMAND_TOPIC,
                CONF_PRESET_MODE_STATE_TOPIC,
                CONF_PRESET_MODE_COMMAND_TOPIC,
                CONF_OSCILLATION_STATE_TOPIC,
                CONF_OSCILLATION_COMMAND_TOPIC,
            )
        }
        self._payload = {
            "STATE_ON": config[CONF_PAYLOAD_ON],
            "STATE_OFF": config[CONF_PAYLOAD_OFF],
            "OSCILLATE_ON_PAYLOAD": config[CONF_PAYLOAD_OSCILLATION_ON],
            "OSCILLATE_OFF_PAYLOAD": config[CONF_PAYLOAD_OSCILLATION_OFF],
            "PERCENTAGE_RESET": config[CONF_PAYLOAD_RESET_PERCENTAGE],
            "PRESET_MODE_RESET": config[CONF_PAYLOAD_RESET_PRESET_MODE],
        }

        self._feature_percentage = CONF_PERCENTAGE_COMMAND_TOPIC in config
        self._feature_preset_mode = CONF_PRESET_MODE_COMMAND_TOPIC in config
        if self._feature_preset_mode:
            self._attr_preset_modes = config[CONF_PRESET_MODES_LIST]
        else:
            self._attr_preset_modes = []

        self._attr_speed_count = (
            min(int_states_in_range(self._speed_range), 100)
            if self._feature_percentage
            else 100
        )

        optimistic = config[CONF_OPTIMISTIC]
        self._optimistic = optimistic or self._topic[CONF_STATE_TOPIC] is None
        self._attr_assumed_state = bool(self._optimistic)
        self._optimistic_direction = (
            optimistic or self._topic[CONF_DIRECTION_STATE_TOPIC] is None
        )
        self._optimistic_oscillation = (
            optimistic or self._topic[CONF_OSCILLATION_STATE_TOPIC] is None
        )
        self._optimistic_percentage = (
            optimistic or self._topic[CONF_PERCENTAGE_STATE_TOPIC] is None
        )
        self._optimistic_preset_mode = (
            optimistic or self._topic[CONF_PRESET_MODE_STATE_TOPIC] is None
        )

        self._attr_supported_features = (
            FanEntityFeature.TURN_OFF | FanEntityFeature.TURN_ON
        )
        self._attr_supported_features |= (
            self._topic[CONF_OSCILLATION_COMMAND_TOPIC] is not None
            and FanEntityFeature.OSCILLATE
        )
        self._attr_supported_features |= (
            self._topic[CONF_DIRECTION_COMMAND_TOPIC] is not None
            and FanEntityFeature.DIRECTION
        )
        if self._feature_percentage:
            self._attr_supported_features |= FanEntityFeature.SET_SPEED
        if self._feature_preset_mode:
            self._attr_supported_features |= FanEntityFeature.PRESET_MODE

        command_templates: dict[str, Template | None] = {
            CONF_STATE: config.get(CONF_COMMAND_TEMPLATE),
            ATTR_DIRECTION: config.get(CONF_DIRECTION_COMMAND_TEMPLATE),
            ATTR_PERCENTAGE: config.get(CONF_PERCENTAGE_COMMAND_TEMPLATE),
            ATTR_PRESET_MODE: config.get(CONF_PRESET_MODE_COMMAND_TEMPLATE),
            ATTR_OSCILLATING: config.get(CONF_OSCILLATION_COMMAND_TEMPLATE),
        }
        self._command_templates = {
            key: MqttCommandTemplate(tpl, entity=self).async_render
            for key, tpl in command_templates.items()
        }

        value_templates: dict[str, Template | None] = {
            CONF_STATE: config.get(CONF_STATE_VALUE_TEMPLATE),
            ATTR_DIRECTION: config.get(CONF_DIRECTION_VALUE_TEMPLATE),
            ATTR_PERCENTAGE: config.get(CONF_PERCENTAGE_VALUE_TEMPLATE),
            ATTR_PRESET_MODE: config.get(CONF_PRESET_MODE_VALUE_TEMPLATE),
            ATTR_OSCILLATING: config.get(CONF_OSCILLATION_VALUE_TEMPLATE),
        }
        self._value_templates = {
            key: MqttValueTemplate(
                tpl, entity=self
            ).async_render_with_possible_json_value
            for key, tpl in value_templates.items()
        }