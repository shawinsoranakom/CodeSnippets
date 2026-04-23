async def _async_device_connect_task(self) -> bool:
        """Connect to a Shelly device task."""
        LOGGER.debug("Connecting to Shelly Device - %s", self.name)
        try:
            await self.device.initialize()
            update_device_fw_info(self.hass, self.device, self.config_entry)
        except (DeviceConnectionError, MacAddressMismatchError) as err:
            LOGGER.debug(
                "Error connecting to Shelly device %s, error: %r", self.name, err
            )
            return False
        except InvalidAuthError:
            self.config_entry.async_start_reauth(self.hass)
            return False

        if not self.device.firmware_supported:
            async_create_issue_unsupported_firmware(self.hass, self.config_entry)
            return False

        if not self._pending_platforms:
            return True

        LOGGER.debug("Device %s is online, resuming setup", self.name)
        platforms = self._pending_platforms
        self._pending_platforms = None

        data = {**self.config_entry.data}

        # Update sleep_period
        old_sleep_period = data[CONF_SLEEP_PERIOD]
        if isinstance(self.device, RpcDevice):
            new_sleep_period = get_rpc_device_wakeup_period(self.device.status)
        elif isinstance(self.device, BlockDevice):
            new_sleep_period = get_block_device_sleep_period(self.device.settings)

        if new_sleep_period != old_sleep_period:
            data[CONF_SLEEP_PERIOD] = new_sleep_period
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)

        # Resume platform setup
        await self.hass.config_entries.async_forward_entry_setups(
            self.config_entry, platforms
        )

        return True