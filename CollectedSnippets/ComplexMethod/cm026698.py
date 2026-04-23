async def on_notification_notification(
        self, notification: WebsocketNotificationTag
    ) -> None:
        """Send notification dispatch."""
        # Try to match the notification type with available WebsocketNotification members
        notification_type = try_parse_enum(WebsocketNotification, notification.value)

        if notification_type in (
            WebsocketNotification.BEOLINK_PEERS,
            WebsocketNotification.BEOLINK_LISTENERS,
            WebsocketNotification.BEOLINK_AVAILABLE_LISTENERS,
        ):
            async_dispatcher_send(
                self.hass,
                f"{DOMAIN}_{self._unique_id}_{WebsocketNotification.BEOLINK}",
            )
        elif notification_type is WebsocketNotification.CONFIGURATION:
            async_dispatcher_send(
                self.hass,
                f"{DOMAIN}_{self._unique_id}_{WebsocketNotification.CONFIGURATION}",
            )
        elif notification_type is WebsocketNotification.REMOTE_MENU_CHANGED:
            async_dispatcher_send(
                self.hass,
                f"{DOMAIN}_{self._unique_id}_{WebsocketNotification.REMOTE_MENU_CHANGED}",
            )

        # This notification is triggered by a remote pairing, unpairing and connecting to a device
        # So the current remote devices have to be compared to available remotes to determine action
        elif notification_type is WebsocketNotification.REMOTE_CONTROL_DEVICES:
            device_registry = dr.async_get(self.hass)
            # Get remote devices connected to the device from Home Assistant
            device_serial_numbers = [
                device.serial_number
                for device in device_registry.devices.get_devices_for_config_entry_id(
                    self.entry.entry_id
                )
                if device.serial_number is not None
                and device.model == BeoModel.BEOREMOTE_ONE
            ]
            # Get paired remotes from device
            remote_serial_numbers = [
                remote.serial_number
                for remote in await get_remotes(self._client)
                if remote.serial_number is not None
            ]
            # Check if number of remote devices correspond to number of paired remotes
            if len(remote_serial_numbers) != len(device_serial_numbers):
                _LOGGER.info(
                    "A Beoremote One has been paired or unpaired to %s. Reloading config entry to add device and entities",
                    self.entry.title,
                )
                self.hass.config_entries.async_schedule_reload(self.entry.entry_id)