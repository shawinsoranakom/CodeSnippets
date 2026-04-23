async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}
        if user_input is not None:
            url = URL(user_input[CONF_URL]).human_repr()[:-1]
            data = {CONF_URL: url}
            self._async_abort_entries_match(data)
            auth_api = Auth(
                session=async_get_clientsession(self.hass),
                base_url=url,
            )
            info_api = Info(auth_api)
            try:
                await info_api.async_update()
            except aiohttp.InvalidUrlClientError:
                errors["base"] = "invalid_url"
            except aiohttp.ClientConnectionError:
                errors["base"] = "cannot_connect"
            else:
                if info_api.serial_number is None:
                    errors["base"] = "missing_device_info"
                else:
                    unique_id = str(info_api.serial_number)
                    if info_api.uid is not None:
                        unique_id = info_api.uid.replace("-", "")
                    await self.async_set_unique_id(unique_id)
                    if self.source == SOURCE_RECONFIGURE:
                        self._abort_if_unique_id_mismatch()
                        return self.async_update_reload_and_abort(
                            self._get_reconfigure_entry(), data_updates=data, title=url
                        )
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=url, data=data)
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )