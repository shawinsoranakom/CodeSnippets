async def async_start(self) -> None:
        """Start the esphome connection manager."""
        hass = self.hass
        entry = self.entry
        entry_data = self.entry_data

        if entry.options.get(CONF_ALLOW_SERVICE_CALLS, DEFAULT_ALLOW_SERVICE_CALLS):
            async_delete_issue(hass, DOMAIN, self.services_issue)

        reconnect_logic = ReconnectLogic(
            client=self.cli,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
            zeroconf_instance=self.zeroconf_instance,
            name=entry.data.get(CONF_DEVICE_NAME, self.host),
            on_connect_error=self.on_connect_error,
        )
        self.reconnect_logic = reconnect_logic

        # Use async_listen instead of async_listen_once so that we don't deregister
        # the callback twice when shutting down Home Assistant.
        # "Unable to remove unknown listener
        # <function EventBus.async_listen_once.<locals>.onetime_listener>"
        # We only close the connection at the last possible moment
        # when the CLOSE event is fired so anything using a Bluetooth
        # proxy has a chance to shut down properly.
        bus = hass.bus
        cleanups = (
            bus.async_listen(EVENT_HOMEASSISTANT_CLOSE, self.on_stop),
            bus.async_listen(EVENT_LOGGING_CHANGED, self._async_handle_logging_changed),
            reconnect_logic.stop_callback,
        )
        entry_data.cleanup_callbacks.extend(cleanups)

        infos, services = await entry_data.async_load_from_store()
        if entry.unique_id:
            await entry_data.async_update_static_infos(
                hass, entry, infos, entry.unique_id.upper()
            )
        _setup_services(hass, entry_data, services)

        if (device_info := entry_data.device_info) is not None:
            self._async_cleanup()
            if device_info.name:
                reconnect_logic.name = device_info.name
            if (
                bluetooth_mac_address := device_info.bluetooth_mac_address
            ) and entry.data.get(CONF_BLUETOOTH_MAC_ADDRESS) != bluetooth_mac_address:
                hass.config_entries.async_update_entry(
                    entry,
                    data={
                        **entry.data,
                        CONF_BLUETOOTH_MAC_ADDRESS: bluetooth_mac_address,
                    },
                )
            if entry.unique_id is None:
                hass.config_entries.async_update_entry(
                    entry, unique_id=format_mac(device_info.mac_address)
                )

        await reconnect_logic.start()