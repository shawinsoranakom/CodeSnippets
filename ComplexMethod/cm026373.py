async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mac = user_input[CONF_MAC].replace(":", "").replace("-", "").upper()
            fumis = Fumis(
                mac=mac,
                password=user_input[CONF_PIN],
                session=async_get_clientsession(self.hass),
            )
            try:
                info = await fumis.update_info()
            except FumisAuthenticationError:
                errors[CONF_PIN] = "invalid_auth"
            except FumisStoveOfflineError:
                errors["base"] = "device_offline"
            except FumisConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(format_mac(mac), raise_on_progress=False)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info.controller.model_name or "Fumis",
                    data={
                        CONF_MAC: mac,
                        CONF_PIN: user_input[CONF_PIN],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_MAC): TextSelector(
                            TextSelectorConfig(autocomplete="off")
                        ),
                        vol.Required(CONF_PIN): TextSelector(
                            TextSelectorConfig(type=TextSelectorType.PASSWORD)
                        ),
                    }
                ),
                user_input,
            ),
            errors=errors,
        )