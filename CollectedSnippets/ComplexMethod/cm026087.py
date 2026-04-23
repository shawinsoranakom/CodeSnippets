async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the start of the config flow."""
        error = None

        if user_input:
            self._async_abort_entries_match({CONF_USERNAME: user_input[CONF_USERNAME]})

            try:
                await self.validate_login_creds(user_input)
            except InvalidCredentials:
                error = {"base": "invalid_auth"}
            except SubaruException as ex:
                _LOGGER.error("Unable to communicate with Subaru API: %s", ex.message)
                return self.async_abort(reason="cannot_connect")
            else:
                if TYPE_CHECKING:
                    assert self.controller
                if not self.controller.device_registered:
                    _LOGGER.debug("2FA validation is required")
                    return await self.async_step_two_factor()
                if self.controller.is_pin_required():
                    return await self.async_step_pin()
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=self.config_data
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=user_input.get(CONF_USERNAME) if user_input else "",
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        default=user_input.get(CONF_PASSWORD) if user_input else "",
                    ): str,
                    vol.Required(
                        CONF_COUNTRY,
                        default=user_input.get(CONF_COUNTRY)
                        if user_input
                        else COUNTRY_USA,
                    ): vol.In([COUNTRY_CAN, COUNTRY_USA]),
                }
            ),
            errors=error,
        )