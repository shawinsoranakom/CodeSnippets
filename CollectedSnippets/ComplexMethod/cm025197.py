def async_get_or_create(self, call_info: CallInfo) -> VoIPDevice:
        """Get or create a device."""
        user_agent = call_info.headers.get("user-agent", "")
        user_agent_parts = user_agent.split()
        if len(user_agent_parts) == 3 and user_agent_parts[0] == "Grandstream":
            manuf = user_agent_parts[0]
            model = user_agent_parts[1]
            fw_version = user_agent_parts[2]
        else:
            manuf = None
            model = user_agent or None
            fw_version = None

        dev_reg = dr.async_get(self.hass)
        if call_info.caller_endpoint is None:
            raise RuntimeError("Could not identify VOIP caller")
        voip_id = call_info.caller_endpoint.uri
        voip_device = self.devices.get(voip_id)

        if voip_device is None:
            # If we couldn't find the device based on SIP URI, see if we can
            # find an old device based on just the host/IP and migrate it
            old_id = call_info.caller_endpoint.host
            voip_device = self.devices.get(old_id)
            if voip_device is not None:
                voip_device.voip_id = voip_id
                self.devices[voip_id] = voip_device
                dev_reg.async_update_device(
                    voip_device.device_id, new_identifiers={(DOMAIN, voip_id)}
                )
                # Migrate entities
                old_prefix = f"{old_id}-"

                def entity_migrator(entry: er.RegistryEntry) -> dict[str, Any] | None:
                    """Migrate entities."""
                    if not entry.unique_id.startswith(old_prefix):
                        return None
                    key = entry.unique_id[len(old_prefix) :]
                    return {
                        "new_unique_id": f"{voip_id}-{key}",
                    }

                self.config_entry.async_create_task(
                    self.hass,
                    er.async_migrate_entries(
                        self.hass, self.config_entry.entry_id, entity_migrator
                    ),
                    f"voip migrating entities {voip_id}",
                )

        # Update device with latest info
        device = dev_reg.async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            identifiers={(DOMAIN, voip_id)},
            name=call_info.caller_endpoint.host,
            manufacturer=manuf,
            model=model,
            sw_version=fw_version,
            configuration_url=f"http://{call_info.caller_ip}",
        )

        if voip_device is not None:
            if (
                call_info.contact_endpoint is not None
                and voip_device.contact != call_info.contact_endpoint
            ):
                # Update VOIP device with contact information from call info
                voip_device.contact = call_info.contact_endpoint
                self.hass.async_create_task(
                    self.device_store.async_update_device(
                        voip_id, call_info.contact_endpoint.sip_header
                    )
                )
            return voip_device

        voip_device = self.devices[voip_id] = VoIPDevice(
            voip_id=voip_id, device_id=device.id, contact=call_info.contact_endpoint
        )
        if call_info.contact_endpoint is not None:
            self.hass.async_create_task(
                self.device_store.async_update_device(
                    voip_id, call_info.contact_endpoint.sip_header
                )
            )

        for listener in self._new_device_listeners:
            listener(voip_device)

        return voip_device