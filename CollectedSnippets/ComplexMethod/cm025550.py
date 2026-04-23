async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        error = None

        if user_input is not None:
            host = user_input[CONF_HOST]
            adb_key = user_input.get(CONF_ADBKEY)
            if CONF_ADB_SERVER_IP in user_input:
                if adb_key:
                    return self._show_setup_form(user_input, "key_and_server")
            else:
                user_input.pop(CONF_ADB_SERVER_PORT, None)

            if adb_key:
                if not await self.hass.async_add_executor_job(_is_file, adb_key):
                    return self._show_setup_form(user_input, "adbkey_not_file")

            self._async_abort_entries_match({CONF_HOST: host})
            error, unique_id = await self._async_check_connection(user_input)
            if error is None:
                if not unique_id:
                    return self.async_abort(reason="invalid_unique_id")

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=host,
                    data=user_input,
                )

        return self._show_setup_form(user_input, error)