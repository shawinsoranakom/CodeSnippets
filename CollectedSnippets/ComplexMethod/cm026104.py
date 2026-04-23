async def async_step_cloud_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the cloud auth step."""
        assert self._discovery_info

        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            fetcher = XiaomiCloudTokenFetch(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD], session
            )
            try:
                device_details = await fetcher.get_device_info(
                    self._discovery_info.address
                )
            except XiaomiCloudInvalidAuthenticationException as ex:
                _LOGGER.debug("Authentication failed: %s", ex, exc_info=True)
                errors = {"base": "auth_failed"}
                description_placeholders = {"error_detail": str(ex)}
            except XiaomiCloudException as ex:
                _LOGGER.debug("Failed to connect to MI API: %s", ex, exc_info=True)
                raise AbortFlow(
                    "api_error", description_placeholders={"error_detail": str(ex)}
                ) from ex
            else:
                if device_details:
                    return await self.async_step_get_encryption_key_4_5(
                        {"bindkey": device_details.bindkey}
                    )
                errors = {"base": "api_device_not_found"}

        user_input = user_input or {}
        return self.async_show_form(
            step_id="cloud_auth",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME, default=user_input.get(CONF_USERNAME)
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            description_placeholders={
                **self.context["title_placeholders"],
                **description_placeholders,
            },
        )