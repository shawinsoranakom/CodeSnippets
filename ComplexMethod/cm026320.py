async def async_step_authorize(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle Authorize step."""
        errors: dict[str, str] = {}
        self.async_stop_display_access_token()

        if user_input is not None and user_input.get(CONF_ACCESS_TOKEN) is not None:
            self.device_config[CONF_ACCESS_TOKEN] = user_input[CONF_ACCESS_TOKEN]

        await self.async_discover_client()
        assert self.client is not None

        await self.async_set_unique_id(self.device_config[CONF_ID])
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: self.device_config[CONF_HOST]}
        )

        try:
            await self.hass.async_add_executor_job(
                self.client._get_session_id  # noqa: SLF001
            )
        except AccessTokenError:
            if user_input is not None:
                errors[CONF_ACCESS_TOKEN] = "invalid_access_token"
        except SessionIdError:
            errors["base"] = "cannot_connect"
        else:
            return await self.async_create_device()

        self._track_interval = async_track_time_interval(
            self.hass,
            self.async_display_access_token,
            DISPLAY_ACCESS_TOKEN_INTERVAL,
            cancel_on_shutdown=True,
        )

        return self.async_show_form(
            step_id="authorize",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_ACCESS_TOKEN): vol.All(str, vol.Length(max=6)),
                }
            ),
            errors=errors,
        )