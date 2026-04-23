async def async_find_device(self, allow_exist: bool = False) -> None:
        """Scan for the selected device to discover services."""
        self.atv, self.atv_identifiers = await device_scan(
            self.hass, self.scan_filter, self.hass.loop
        )
        if not self.atv:
            raise DeviceNotFound

        # Protocols supported by the device are prospects for pairing
        self.protocols_to_pair = deque(
            service.protocol for service in self.atv.services if service.enabled
        )

        dev_info = self.atv.device_info
        self.context["title_placeholders"] = {
            "name": self.atv.name,
            "type": (
                dev_info.raw_model
                if dev_info.model == DeviceModel.Unknown and dev_info.raw_model
                else model_str(dev_info.model)
            ),
        }
        all_identifiers = set(self.atv.all_identifiers)
        discovered_ip_address = str(self.atv.address)
        for entry in self._async_current_entries():
            existing_identifiers = set(
                entry.data.get(CONF_IDENTIFIERS, [entry.unique_id])
            )
            if all_identifiers.isdisjoint(existing_identifiers):
                continue
            combined_identifiers = existing_identifiers | all_identifiers
            if entry.data.get(
                CONF_ADDRESS
            ) != discovered_ip_address or combined_identifiers != set(
                entry.data.get(CONF_IDENTIFIERS, [])
            ):
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        **entry.data,
                        CONF_ADDRESS: discovered_ip_address,
                        CONF_IDENTIFIERS: list(combined_identifiers),
                    },
                )
                # Don't reload ignored entries or in the middle of reauth,
                # e.g. if the user is entering a new PIN
                if entry.source != SOURCE_IGNORE and self.source != SOURCE_REAUTH:
                    self.hass.config_entries.async_schedule_reload(entry.entry_id)
            if not allow_exist:
                raise DeviceAlreadyConfigured