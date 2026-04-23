async def _on_connect(self) -> None:
        """Subscribe to states and list entities on successful API login."""
        entry = self.entry
        unique_id = entry.unique_id
        entry_data = self.entry_data
        reconnect_logic = self.reconnect_logic
        assert reconnect_logic is not None, "Reconnect logic must be set"
        hass = self.hass
        cli = self.cli
        stored_device_name: str | None = entry.data.get(CONF_DEVICE_NAME)
        unique_id_is_mac_address = unique_id and ":" in unique_id
        if entry.options.get(CONF_SUBSCRIBE_LOGS):
            self._async_subscribe_logs(self._async_get_equivalent_log_level())
        device_info, entity_infos, services = await cli.device_info_and_list_entities()

        device_mac = format_mac(device_info.mac_address)
        mac_address_matches = unique_id == device_mac
        if (
            bluetooth_mac_address := device_info.bluetooth_mac_address
        ) and entry.data.get(CONF_BLUETOOTH_MAC_ADDRESS) != bluetooth_mac_address:
            hass.config_entries.async_update_entry(
                entry,
                data={**entry.data, CONF_BLUETOOTH_MAC_ADDRESS: bluetooth_mac_address},
            )
        #
        # Migrate config entry to new unique ID if the current
        # unique id is not a mac address.
        #
        # This was changed in 2023.1
        if not mac_address_matches and not unique_id_is_mac_address:
            hass.config_entries.async_update_entry(entry, unique_id=device_mac)

        issue = DEVICE_CONFLICT_ISSUE_FORMAT.format(entry.entry_id)
        if not mac_address_matches and unique_id_is_mac_address:
            # If the unique id is a mac address
            # and does not match we have the wrong device and we need
            # to abort the connection. This can happen if the DHCP
            # server changes the IP address of the device and we end up
            # connecting to the wrong device.
            if stored_device_name == device_info.name:
                # If the device name matches it might be a device replacement
                # or they made a mistake and flashed the same firmware on
                # multiple devices. In this case we start a repair flow
                # to ask them if its a mistake, or if they want to migrate
                # the config entry to the replacement hardware.
                shared_data = {
                    "name": device_info.name,
                    "mac": format_mac(device_mac),
                    "stored_mac": format_mac(unique_id),
                    "model": device_info.model,
                    "ip": self.host,
                }
                async_create_issue(
                    hass,
                    DOMAIN,
                    issue,
                    is_fixable=True,
                    severity=IssueSeverity.ERROR,
                    translation_key="device_conflict",
                    translation_placeholders=shared_data,
                    data={**shared_data, "entry_id": entry.entry_id},
                )
            _LOGGER.error(
                "Unexpected device found at %s; "
                "expected `%s` with mac address `%s`, "
                "found `%s` with mac address `%s`",
                self.host,
                stored_device_name,
                unique_id,
                device_info.name,
                device_mac,
            )
            await cli.disconnect()
            await reconnect_logic.stop()
            # We don't want to reconnect to the wrong device
            # so we stop the reconnect logic and disconnect
            # the client. When discovery finds the new IP address
            # for the device, the config entry will be updated
            # and we will connect to the correct device when
            # the config entry gets reloaded by the discovery
            # flow.
            return

        async_delete_issue(hass, DOMAIN, issue)
        # Make sure we have the correct device name stored
        # so we can map the device to ESPHome Dashboard config
        # If we got here, we know the mac address matches or we
        # did a migration to the mac address so we can update
        # the device name.
        if stored_device_name != device_info.name:
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_DEVICE_NAME: device_info.name}
            )

        api_version = cli.api_version
        assert api_version is not None, "API version must be set"
        entry_data.async_on_connect(hass, device_info, api_version)

        await self._handle_dynamic_encryption_key(device_info)

        if device_info.name:
            reconnect_logic.name = device_info.name

        if not device_info.friendly_name:
            _LOGGER.info(
                "No `friendly_name` set in the `esphome:` section of the "
                "YAML config for device '%s' (MAC: %s); It's recommended "
                "to add one for easier identification and better alignment "
                "with Home Assistant naming conventions",
                device_info.name,
                device_mac,
            )
        # Build device_id_to_name mapping for efficient lookup
        entry_data.device_id_to_name = {
            sub_device.device_id: sub_device.name or device_info.name
            for sub_device in device_info.devices
        }
        self.device_id = _async_setup_device_registry(hass, entry, entry_data)

        entry_data.async_update_device_state()
        await entry_data.async_update_static_infos(
            hass, entry, entity_infos, device_info.mac_address
        )
        _setup_services(hass, entry_data, services)

        if device_info.bluetooth_proxy_feature_flags_compat(api_version):
            entry_data.disconnect_callbacks.add(
                async_connect_scanner(
                    hass, entry_data, cli, device_info, self.device_id
                )
            )
        else:
            bluetooth.async_remove_scanner(
                hass, device_info.bluetooth_mac_address or device_info.mac_address
            )

        if device_info.voice_assistant_feature_flags_compat(api_version) and (
            Platform.ASSIST_SATELLITE not in entry_data.loaded_platforms
        ):
            # Create assist satellite entity
            await self.hass.config_entries.async_forward_entry_setups(
                self.entry, [Platform.ASSIST_SATELLITE]
            )
            entry_data.loaded_platforms.add(Platform.ASSIST_SATELLITE)

        if device_info.zwave_proxy_feature_flags:
            entry_data.disconnect_callbacks.add(
                cli.subscribe_zwave_proxy_request(self._async_zwave_proxy_request)
            )

        cli.subscribe_home_assistant_states_and_services(
            on_state=entry_data.async_update_state,
            on_service_call=self.async_on_service_call,
            on_state_sub=self.async_on_state_subscription,
            on_state_request=self.async_on_state_request,
        )

        entry_data.async_save_to_store()
        _async_check_firmware_version(hass, device_info, api_version)
        _async_check_using_api_password(hass, device_info, bool(self.password))