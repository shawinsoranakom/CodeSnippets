async def async_step_dhcp_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle DHCP discovery confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            fumis = Fumis(
                mac=self._discovered_mac,
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
                return self.async_create_entry(
                    title=info.controller.model_name or "Fumis",
                    data={
                        CONF_MAC: self._discovered_mac,
                        CONF_PIN: user_input[CONF_PIN],
                    },
                )

        return self.async_show_form(
            step_id="dhcp_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PIN): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            errors=errors,
        )