async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            self.config = {
                CONF_HOST: user_input[CONF_HOST],
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_PORT: user_input.get(CONF_PORT),
                CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL),
                CONF_SITE_ID: DEFAULT_SITE_ID,
            }

            try:
                hub = await get_unifi_api(self.hass, MappingProxyType(self.config))
                await hub.sites.update()
                self.sites = hub.sites

            except AuthenticationRequired:
                errors["base"] = "faulty_credentials"

            except CannotConnect:
                errors["base"] = "service_unavailable"

            else:
                if (
                    self.source == SOURCE_REAUTH
                    and (
                        (reauth_unique_id := self._get_reauth_entry().unique_id)
                        is not None
                    )
                    and reauth_unique_id in self.sites
                ):
                    return await self.async_step_site({CONF_SITE_ID: reauth_unique_id})

                return await self.async_step_site()

        if not (host := self.config.get(CONF_HOST, "")) and await _async_discover_unifi(
            self.hass
        ):
            host = "unifi"

        data = self.reauth_schema or {
            vol.Required(CONF_HOST, default=host): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(
                CONF_PORT, default=self.config.get(CONF_PORT, DEFAULT_PORT)
            ): int,
            vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data),
            errors=errors,
        )