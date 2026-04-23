async def validate_common(
        self,
        gw_type: ConfGatewayType,
        errors: dict[str, str],
        user_input: dict[str, Any],
    ) -> dict[str, str]:
        """Validate parameters common to all gateway types."""
        errors.update(_validate_version(user_input[CONF_VERSION]))

        if gw_type != CONF_GATEWAY_TYPE_MQTT:
            if gw_type == CONF_GATEWAY_TYPE_TCP:
                verification_func = is_socket_address
            else:
                verification_func = is_serial_port

            try:
                await self.hass.async_add_executor_job(
                    verification_func, user_input[CONF_DEVICE]
                )
            except vol.Invalid:
                errors[CONF_DEVICE] = (
                    "invalid_ip"
                    if gw_type == CONF_GATEWAY_TYPE_TCP
                    else "invalid_serial"
                )
        if CONF_PERSISTENCE_FILE in user_input:
            try:
                is_persistence_file(user_input[CONF_PERSISTENCE_FILE])
            except vol.Invalid:
                errors[CONF_PERSISTENCE_FILE] = "invalid_persistence_file"
            else:
                real_persistence_path = user_input[CONF_PERSISTENCE_FILE] = (
                    self._normalize_persistence_file(user_input[CONF_PERSISTENCE_FILE])
                )
                for other_entry in self._async_current_entries():
                    if CONF_PERSISTENCE_FILE not in other_entry.data:
                        continue
                    if real_persistence_path == self._normalize_persistence_file(
                        other_entry.data[CONF_PERSISTENCE_FILE]
                    ):
                        errors[CONF_PERSISTENCE_FILE] = "duplicate_persistence_file"
                        break

        if not errors:
            for other_entry in self._async_current_entries():
                if _is_same_device(gw_type, user_input, other_entry):
                    errors["base"] = "already_configured"
                    break

        # if no errors so far, try to connect
        if not errors and not await try_connect(self.hass, gw_type, user_input):
            errors["base"] = "cannot_connect"

        return errors