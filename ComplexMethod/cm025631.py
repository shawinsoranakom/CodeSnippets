async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}
        host = (user_input or {}).get(CONF_HOST) or self.ip_address or ""

        if user_input is not None:
            envoy = await validate_input(
                self.hass,
                host,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                errors,
                description_placeholders,
            )
            if not errors:
                name = self._async_envoy_name()

                if not self.unique_id:
                    await self.async_set_unique_id(envoy.serial_number)
                    name = self._async_envoy_name()

                if self.unique_id:
                    # If envoy exists in configuration update fields and exit
                    self._abort_if_unique_id_configured(
                        {
                            CONF_HOST: host,
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                        },
                        error="reauth_successful",
                    )

                # CONF_NAME is still set for legacy backwards compatibility
                return self.async_create_entry(
                    title=name, data={CONF_HOST: host, CONF_NAME: name} | user_input
                )

        if self.unique_id:
            self.context["title_placeholders"] = {
                CONF_SERIAL: self.unique_id,
                CONF_HOST: host,
            }
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                self._async_generate_schema(),
                without_avoid_reflect_keys(user_input or {}),
            ),
            description_placeholders=description_placeholders,
            errors=errors,
        )