async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        assert self.ip_address
        assert self.product_name
        assert self.product_type
        assert self.serial

        errors: dict[str, str] | None = None
        if user_input is not None or not onboarding.async_is_onboarded(self.hass):
            try:
                await async_try_connect(self.ip_address)
            except RecoverableError as ex:
                LOGGER.error(ex)
                errors = {"base": ex.error_code}
            except UnauthorizedError:
                return await self.async_step_authorize()
            else:
                return self.async_create_entry(
                    title=self.product_name,
                    data={CONF_IP_ADDRESS: self.ip_address},
                )

        self._set_confirm_only()

        # We won't be adding mac/serial to the title for devices
        # that users generally don't have multiple of.
        name = self.product_name
        if self.product_type not in ["HWE-P1", "HWE-WTR"]:
            name = f"{name} ({self.serial})"
        self.context["title_placeholders"] = {"name": name}

        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={
                CONF_PRODUCT_TYPE: self.product_type,
                CONF_SERIAL: self.serial,
                CONF_IP_ADDRESS: self.ip_address,
            },
            errors=errors,
        )