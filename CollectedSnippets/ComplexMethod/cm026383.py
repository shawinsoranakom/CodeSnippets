async def async_add_unique_device(
        self, hass: HomeAssistant, wemo: pywemo.WeMoDevice
    ) -> None:
        """Add a WeMo device to hass if it has not already been added."""
        if wemo.serial_number in self._added_serial_numbers:
            return

        try:
            coordinator = await async_register_device(hass, self._config_entry, wemo)
        except pywemo.PyWeMoException as err:
            if wemo.serial_number not in self._failed_serial_numbers:
                self._failed_serial_numbers.add(wemo.serial_number)
                _LOGGER.error(
                    "Unable to add WeMo %s %s: %s", repr(wemo), wemo.host, err
                )
            return

        platforms = set(WEMO_MODEL_DISPATCH.get(wemo.model_name, [Platform.SWITCH]))
        platforms.add(Platform.SENSOR)
        platforms_to_load: list[Platform] = []
        for platform in platforms:
            # Three cases:
            # - Platform is loaded, dispatch discovery
            # - Platform is being loaded, add to backlog
            # - First time we see platform, we need to load it and initialize the backlog

            if platform in self._dispatch_callbacks:
                await self._dispatch_callbacks[platform](coordinator)
            elif platform in self._dispatch_backlog:
                self._dispatch_backlog[platform].append(coordinator)
            else:
                self._dispatch_backlog[platform] = [coordinator]
                platforms_to_load.append(platform)

        self._added_serial_numbers.add(wemo.serial_number)
        self._failed_serial_numbers.discard(wemo.serial_number)

        if platforms_to_load:
            await hass.config_entries.async_forward_entry_setups(
                self._config_entry, platforms_to_load
            )