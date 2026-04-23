async def async_step_multiple_adapters(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            assert self._adapters is not None
            adapter = user_input[CONF_ADAPTER]
            details = self._adapters[adapter]
            address = details[ADAPTER_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=adapter_title(adapter, details), data={}
            )

        configured_addresses = self._async_current_ids(include_ignore=False)
        bluetooth_adapters = get_adapters()
        await bluetooth_adapters.refresh()
        self._adapters = bluetooth_adapters.adapters
        system = platform.system()
        unconfigured_adapters = [
            adapter
            for adapter, details in self._adapters.items()
            if details[ADAPTER_ADDRESS] not in configured_addresses
            # DEFAULT_ADDRESS is perfectly valid on MacOS but on
            # Linux it means the adapter is not yet configured
            # or crashed
            and not (system == "Linux" and details[ADAPTER_ADDRESS] == DEFAULT_ADDRESS)
        ]
        if not unconfigured_adapters:
            return self.async_abort(
                reason="no_adapters",
            )
        if len(unconfigured_adapters) == 1:
            self._adapter = list(self._adapters)[0]
            self._details = self._adapters[self._adapter]
            self._async_set_adapter_info(self._adapter, self._details)
            return await self.async_step_single_adapter()

        return self.async_show_form(
            step_id="multiple_adapters",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADAPTER): vol.In(
                        {
                            adapter: adapter_display_info(
                                adapter, self._adapters[adapter]
                            )
                            for adapter in sorted(unconfigured_adapters)
                        }
                    ),
                }
            ),
        )