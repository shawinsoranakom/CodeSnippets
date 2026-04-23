async def async_update(self) -> None:
        """Update state of device."""
        try:
            power_state = await self._projector.get_power()
        except ProjectorUnavailableError as ex:
            _LOGGER.debug("Projector is unavailable: %s", ex)
            self._attr_available = False
            return
        if not power_state:
            self._attr_available = False
            return
        _LOGGER.debug("Projector status: %s", power_state)
        self._attr_available = True
        if power_state == EPSON_CODES[POWER]:
            self._attr_state = MediaPlayerState.ON
            if await self.set_unique_id():
                return
            self._attr_source_list = list(DEFAULT_SOURCES.values())
            cmode = await self._projector.get_property(CMODE)
            self._cmode = CMODE_LIST.get(cmode, self._cmode)
            source = await self._projector.get_property(SOURCE)
            self._attr_source = SOURCE_LIST.get(source, self._attr_source)
            if volume := await self._projector.get_property(VOLUME):
                try:
                    self._attr_volume_level = float(volume)
                except ValueError:
                    self._attr_volume_level = None
        elif power_state in BUSY_CODES:
            self._attr_state = MediaPlayerState.ON
        else:
            self._attr_state = MediaPlayerState.OFF