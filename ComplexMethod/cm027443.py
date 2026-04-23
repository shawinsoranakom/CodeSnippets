async def async_step_user(
        self, user_input: Mapping[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow start."""
        LOGGER.debug("async_step_user: user_input: %s", user_input)

        if user_input is not None:
            # Ensure wanted device was discovered.
            assert self._discoveries
            discovery = next(
                iter(
                    discovery
                    for discovery in self._discoveries.values()
                    if discovery.ssdp_usn == user_input["unique_id"]
                )
            )
            await self.async_set_unique_id(discovery.ssdp_usn, raise_on_progress=False)
            return await self._async_create_entry_from_discovery(discovery)

        # Discover devices.
        discoveries = await _async_discovered_igd_devices(self.hass)

        # Store discoveries which have not been configured.
        current_unique_ids = {
            entry.unique_id for entry in self._async_current_entries()
        }
        for discovery in discoveries:
            if (
                _is_complete_discovery(discovery)
                and _is_igd_device(discovery)
                and discovery.ssdp_usn not in current_unique_ids
            ):
                self._add_discovery(discovery)

        # Ensure anything to add.
        if not self._discoveries:
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema(
            {
                vol.Required("unique_id"): vol.In(
                    {
                        discovery.ssdp_usn: _friendly_name_from_discovery(discovery)
                        for discovery in self._discoveries.values()
                    }
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )