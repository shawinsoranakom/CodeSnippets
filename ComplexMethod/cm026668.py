async def async_step_gw_mqtt(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create a config entry for a mqtt gateway."""
        # Naive check that doesn't consider config entry state.
        if MQTT_DOMAIN not in self.hass.config.components:
            return self.async_abort(reason="mqtt_required")

        gw_type = self._gw_type = CONF_GATEWAY_TYPE_MQTT
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_DEVICE] = MQTT_COMPONENT

            try:
                valid_subscribe_topic(user_input[CONF_TOPIC_IN_PREFIX])
            except vol.Invalid:
                errors[CONF_TOPIC_IN_PREFIX] = "invalid_subscribe_topic"
            else:
                if self._check_topic_exists(user_input[CONF_TOPIC_IN_PREFIX]):
                    errors[CONF_TOPIC_IN_PREFIX] = "duplicate_topic"

            try:
                valid_publish_topic(user_input[CONF_TOPIC_OUT_PREFIX])
            except vol.Invalid:
                errors[CONF_TOPIC_OUT_PREFIX] = "invalid_publish_topic"
            if not errors:
                if (
                    user_input[CONF_TOPIC_IN_PREFIX]
                    == user_input[CONF_TOPIC_OUT_PREFIX]
                ):
                    errors[CONF_TOPIC_OUT_PREFIX] = "same_topic"
                elif self._check_topic_exists(user_input[CONF_TOPIC_OUT_PREFIX]):
                    errors[CONF_TOPIC_OUT_PREFIX] = "duplicate_topic"

            errors.update(await self.validate_common(gw_type, errors, user_input))
            if not errors:
                return self._async_create_entry(user_input)

        user_input = user_input or {}
        schema: VolDictType = {
            vol.Required(
                CONF_TOPIC_IN_PREFIX, default=user_input.get(CONF_TOPIC_IN_PREFIX, "")
            ): str,
            vol.Required(
                CONF_TOPIC_OUT_PREFIX, default=user_input.get(CONF_TOPIC_OUT_PREFIX, "")
            ): str,
            vol.Required(CONF_RETAIN, default=user_input.get(CONF_RETAIN, True)): bool,
        }
        schema.update(_get_schema_common(user_input))

        return self.async_show_form(
            step_id="gw_mqtt", data_schema=vol.Schema(schema), errors=errors
        )