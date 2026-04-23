def _setup_from_config(self, config: ConfigType) -> None:
        """Set up cover from config."""
        self._pos_range = (config[CONF_POSITION_CLOSED] + 1, config[CONF_POSITION_OPEN])
        self._tilt_range = (config[CONF_TILT_MIN] + 1, config[CONF_TILT_MAX])
        self._tilt_closed_percentage = ranged_value_to_percentage(
            self._tilt_range, config[CONF_TILT_CLOSED_POSITION]
        )
        self._tilt_open_percentage = ranged_value_to_percentage(
            self._tilt_range, config[CONF_TILT_OPEN_POSITION]
        )
        no_position = (
            config.get(CONF_SET_POSITION_TOPIC) is None
            and config.get(CONF_GET_POSITION_TOPIC) is None
        )
        no_state = (
            config.get(CONF_COMMAND_TOPIC) is None
            and config.get(CONF_STATE_TOPIC) is None
        )
        no_tilt = (
            config.get(CONF_TILT_COMMAND_TOPIC) is None
            and config.get(CONF_TILT_STATUS_TOPIC) is None
        )
        optimistic_position = (
            config.get(CONF_SET_POSITION_TOPIC) is not None
            and config.get(CONF_GET_POSITION_TOPIC) is None
        )
        optimistic_state = (
            config.get(CONF_COMMAND_TOPIC) is not None
            and config.get(CONF_STATE_TOPIC) is None
        )
        optimistic_tilt = (
            config.get(CONF_TILT_COMMAND_TOPIC) is not None
            and config.get(CONF_TILT_STATUS_TOPIC) is None
        )

        self._optimistic = config[CONF_OPTIMISTIC] or (
            (no_position or optimistic_position)
            and (no_state or optimistic_state)
            and (no_tilt or optimistic_tilt)
        )
        self._attr_assumed_state = self._optimistic

        self._tilt_optimistic = (
            config[CONF_TILT_STATE_OPTIMISTIC]
            or config.get(CONF_TILT_STATUS_TOPIC) is None
        )

        template_config_attributes = {
            "position_open": config[CONF_POSITION_OPEN],
            "position_closed": config[CONF_POSITION_CLOSED],
            "tilt_min": config[CONF_TILT_MIN],
            "tilt_max": config[CONF_TILT_MAX],
        }

        self._value_template = MqttValueTemplate(
            config.get(CONF_VALUE_TEMPLATE), entity=self
        ).async_render_with_possible_json_value

        self._set_position_template = MqttCommandTemplate(
            config.get(CONF_SET_POSITION_TEMPLATE), entity=self
        ).async_render

        self._get_position_template = MqttValueTemplate(
            config.get(CONF_GET_POSITION_TEMPLATE),
            entity=self,
            config_attributes=template_config_attributes,
        ).async_render_with_possible_json_value

        self._set_tilt_template = MqttCommandTemplate(
            self._config.get(CONF_TILT_COMMAND_TEMPLATE), entity=self
        ).async_render

        self._tilt_status_template = MqttValueTemplate(
            self._config.get(CONF_TILT_STATUS_TEMPLATE),
            entity=self,
            config_attributes=template_config_attributes,
        ).async_render_with_possible_json_value

        self._attr_device_class = self._config.get(CONF_DEVICE_CLASS)

        supported_features = CoverEntityFeature(0)
        if self._config.get(CONF_COMMAND_TOPIC) is not None:
            if self._config.get(CONF_PAYLOAD_OPEN) is not None:
                supported_features |= CoverEntityFeature.OPEN
            if self._config.get(CONF_PAYLOAD_CLOSE) is not None:
                supported_features |= CoverEntityFeature.CLOSE
            if self._config.get(CONF_PAYLOAD_STOP) is not None:
                supported_features |= CoverEntityFeature.STOP

        if self._config.get(CONF_SET_POSITION_TOPIC) is not None:
            supported_features |= CoverEntityFeature.SET_POSITION

        if self._config.get(CONF_TILT_COMMAND_TOPIC) is not None:
            supported_features |= TILT_FEATURES

        self._attr_supported_features = supported_features