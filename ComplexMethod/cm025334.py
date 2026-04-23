def _async_handle_update(
        self, device_: RpcDevice, update_type: RpcUpdateType
    ) -> None:
        """Handle device update."""
        LOGGER.debug("Shelly %s handle update, type: %s", self.name, update_type)
        if update_type is RpcUpdateType.ONLINE:
            self._came_online_once = True
            self._async_handle_rpc_device_online()
        elif update_type is RpcUpdateType.INITIALIZED:
            self.config_entry.async_create_background_task(
                self.hass, self._async_connected(), "rpc device init", eager_start=True
            )
            # Make sure entities are marked available
            self.async_set_updated_data(None)
        elif update_type is RpcUpdateType.DISCONNECTED:
            self.config_entry.async_create_background_task(
                self.hass,
                self._async_disconnected(True),
                "rpc device disconnected",
                eager_start=True,
            )
            # Make sure entities are marked as unavailable
            self.async_set_updated_data(None)
        elif update_type is RpcUpdateType.STATUS:
            self.async_set_updated_data(None)
            if self.sleep_period:
                update_device_fw_info(self.hass, self.device, self.config_entry)
        elif update_type is RpcUpdateType.EVENT and (event := self.device.event):
            self._async_device_event_handler(event)