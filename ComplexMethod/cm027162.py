async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            if not (host := user_input[CONF_HOST]):
                return await self.async_step_pick_device()
            if not is_ip_address(user_input[CONF_HOST]):
                errors["base"] = "no_ip"
            else:
                bulb = wizlight(host)
                try:
                    bulbtype = await bulb.get_bulbtype()
                    mac = await bulb.getMac()
                except WizLightTimeOutError:
                    errors["base"] = "bulb_time_out"
                except ConnectionRefusedError:
                    errors["base"] = "cannot_connect"
                except WizLightConnectionError:
                    errors["base"] = "no_wiz_light"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(mac, raise_on_progress=False)
                    self._abort_if_unique_id_configured(
                        updates={CONF_HOST: user_input[CONF_HOST]}
                    )
                    name = name_from_bulb_type_and_mac(bulbtype, mac)
                    return self.async_create_entry(
                        title=name,
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Optional(CONF_HOST, default=""): str}),
            errors=errors,
        )