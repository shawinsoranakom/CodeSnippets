async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            host = _normalize_host(user_input[CONF_HOST])
            try:
                device = await self._async_get_device(host)
            except WLEDUnsupportedVersionError:
                errors["base"] = "unsupported_version"
            except WLEDConnectionError:
                errors["base"] = "cannot_connect"
            else:
                mac_address = normalize_mac_address(device.info.mac_address)
                await self.async_set_unique_id(mac_address, raise_on_progress=False)
                if self.source == SOURCE_RECONFIGURE:
                    entry = self._get_reconfigure_entry()
                    self._abort_if_unique_id_mismatch(
                        reason="unique_id_mismatch",
                        description_placeholders={
                            "expected_mac": format_mac(entry.unique_id).upper(),
                            "actual_mac": mac_address.upper(),
                        },
                    )
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={CONF_HOST: host},
                    )
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(
                    title=device.info.name,
                    data={CONF_HOST: host},
                )
        data_schema = vol.Schema({vol.Required(CONF_HOST): str})
        if self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            data_schema = self.add_suggested_values_to_schema(
                data_schema,
                entry.data,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors or {},
        )