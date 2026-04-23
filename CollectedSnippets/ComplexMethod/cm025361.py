async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_load_data(user_input)
            try:
                self._remote = await self.hass.async_add_executor_job(
                    partial(RemoteControl, self._data[CONF_HOST], self._data[CONF_PORT])
                )
                assert self._remote is not None
                self._data[ATTR_DEVICE_INFO] = await self.hass.async_add_executor_job(
                    self._remote.get_device_info
                )
            except (URLError, SOAPError, OSError) as err:
                _LOGGER.error("Could not establish remote connection: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("An unknown error occurred")
                return self.async_abort(reason="unknown")
            else:
                await self.async_set_unique_id(self._data[ATTR_DEVICE_INFO][ATTR_UDN])
                self._abort_if_unique_id_configured()

                if self._data[CONF_NAME] == DEFAULT_NAME:
                    self._data[CONF_NAME] = self._data[ATTR_DEVICE_INFO][
                        ATTR_FRIENDLY_NAME
                    ].replace("_", " ")

                if self._remote.type == TV_TYPE_ENCRYPTED:
                    return await self.async_step_pairing()

                return self.async_create_entry(
                    title=self._data[CONF_NAME],
                    data=self._data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=self._data[CONF_HOST]
                        if self._data[CONF_HOST] is not None
                        else "",
                    ): str,
                    vol.Optional(
                        CONF_NAME,
                        default=self._data[CONF_NAME]
                        if self._data[CONF_NAME] is not None
                        else DEFAULT_NAME,
                    ): str,
                }
            ),
            errors=errors,
        )