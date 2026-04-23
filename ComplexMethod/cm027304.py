def _setup_from_config(self, config: ConfigType) -> None:
        """(Re)Setup the entity."""

        state_on: str | None = config.get(CONF_STATE_ON)
        self._state_on = state_on or config[CONF_PAYLOAD_ON]

        state_off: str | None = config.get(CONF_STATE_OFF)
        self._state_off = state_off or config[CONF_PAYLOAD_OFF]

        self._extra_attributes = {}

        _supported_features = SUPPORTED_BASE
        if config[CONF_SUPPORT_DURATION]:
            _supported_features |= SirenEntityFeature.DURATION
            self._extra_attributes[ATTR_DURATION] = None

        if config.get(CONF_AVAILABLE_TONES):
            _supported_features |= SirenEntityFeature.TONES
            self._attr_available_tones = config[CONF_AVAILABLE_TONES]
            self._extra_attributes[ATTR_TONE] = None

        if config[CONF_SUPPORT_VOLUME_SET]:
            _supported_features |= SirenEntityFeature.VOLUME_SET
            self._extra_attributes[ATTR_VOLUME_LEVEL] = None

        self._attr_supported_features = _supported_features
        self._optimistic = config[CONF_OPTIMISTIC] or CONF_STATE_TOPIC not in config
        self._attr_assumed_state = bool(self._optimistic)
        self._attr_is_on = False if self._optimistic else None

        command_template: Template | None = config.get(CONF_COMMAND_TEMPLATE)
        command_off_template: Template | None = (
            config.get(CONF_COMMAND_OFF_TEMPLATE) or command_template
        )
        self._command_templates = {
            CONF_COMMAND_TEMPLATE: MqttCommandTemplate(
                command_template, entity=self
            ).async_render
            if command_template
            else None,
            CONF_COMMAND_OFF_TEMPLATE: MqttCommandTemplate(
                command_off_template, entity=self
            ).async_render
            if command_off_template
            else None,
        }
        self._value_template = MqttValueTemplate(
            config.get(CONF_STATE_VALUE_TEMPLATE),
            entity=self,
        ).async_render_with_possible_json_value