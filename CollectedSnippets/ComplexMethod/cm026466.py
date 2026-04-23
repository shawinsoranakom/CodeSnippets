async def async_step_manual_entry(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user's choice of entering the device manually."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if self.discovered:
                host = self.discovered_host
            elif self.source == SOURCE_REAUTH:
                host = self._get_reauth_entry().data[CONF_HOST]
            else:
                host = user_input[CONF_HOST]

            try:
                return await self._async_step_create_entry(
                    host, user_input[CONF_API_KEY]
                )
            except AbortFlow:
                raise
            except LaMetricConnectionError as ex:
                LOGGER.error("Error connecting to LaMetric: %s", ex)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected error occurred")
                errors["base"] = "unknown"

        # Don't ask for a host if it was discovered
        schema = {
            vol.Required(CONF_API_KEY): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            )
        }
        if not self.discovered and self.source != SOURCE_REAUTH:
            schema = {vol.Required(CONF_HOST): TextSelector()} | schema

        return self.async_show_form(
            step_id="manual_entry",
            data_schema=vol.Schema(schema),
            description_placeholders={
                "devices_url": DEVICES_URL,
            },
            errors=errors,
        )