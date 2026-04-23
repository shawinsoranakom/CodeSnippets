async def async_step_pin(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle second part of config flow, if required."""
        error = None
        if TYPE_CHECKING:
            assert self.controller
        if user_input and self.controller.update_saved_pin(user_input[CONF_PIN]):
            try:
                vol.Match(r"[0-9]{4}")(user_input[CONF_PIN])
                await self.controller.test_pin()
            except vol.Invalid:
                error = {"base": "bad_pin_format"}
            except InvalidPIN:
                error = {"base": "incorrect_pin"}
            else:
                _LOGGER.debug("PIN successfully tested")
                self.config_data.update(user_input)
                return self.async_create_entry(
                    title=self.config_data[CONF_USERNAME], data=self.config_data
                )
        return self.async_show_form(step_id="pin", data_schema=PIN_SCHEMA, errors=error)