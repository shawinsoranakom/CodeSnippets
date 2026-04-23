async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        errors: dict[str, str] = {}
        discovery_info = self._discovered_device

        form_data = {
            CONF_HOST: discovery_info["direct_connect_domain"]
            or discovery_info["source_ip"],
            CONF_PORT: DEFAULT_PORT,
            CONF_VERIFY_SSL: bool(discovery_info["direct_connect_domain"]),
            CONF_USERNAME: "",
            CONF_PASSWORD: "",
        }

        if user_input is not None:
            # Merge user input with discovery info
            merged_input = {**form_data, **user_input}
            nvr_data = None
            if discovery_info["direct_connect_domain"]:
                merged_input[CONF_HOST] = discovery_info["direct_connect_domain"]
                merged_input[CONF_VERIFY_SSL] = True
                nvr_data, errors = await self._async_get_nvr_data(merged_input)
            if not nvr_data or errors:
                merged_input[CONF_HOST] = discovery_info["source_ip"]
                merged_input[CONF_VERIFY_SSL] = False
                nvr_data, errors = await self._async_get_nvr_data(merged_input)
            if nvr_data and not errors:
                return self._async_create_entry(nvr_data.display_name, merged_input)
            # Preserve user input for form re-display, but keep discovery info
            form_data = {
                CONF_HOST: merged_input[CONF_HOST],
                CONF_PORT: merged_input[CONF_PORT],
                CONF_VERIFY_SSL: merged_input[CONF_VERIFY_SSL],
                CONF_USERNAME: user_input.get(CONF_USERNAME, ""),
                CONF_PASSWORD: user_input.get(CONF_PASSWORD, ""),
            }
            if CONF_API_KEY in user_input:
                form_data[CONF_API_KEY] = user_input[CONF_API_KEY]

        placeholders = {
            "name": discovery_info["hostname"]
            or discovery_info["platform"]
            or f"NVR {_async_short_mac(discovery_info['hw_addr'])}",
            "ip_address": discovery_info["source_ip"],
        }
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={
                **placeholders,
                "local_user_documentation_url": await async_local_user_documentation_url(
                    self.hass
                ),
            },
            data_schema=self.add_suggested_values_to_schema(
                DISCOVERY_SCHEMA, form_data
            ),
            errors=errors,
        )