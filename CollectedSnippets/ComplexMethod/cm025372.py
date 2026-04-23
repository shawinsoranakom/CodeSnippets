async def async_update(self) -> None:
        """Fetch updates from the device."""
        try:
            if self._sysinfo is None:
                self._sysinfo = await self._dev.get_system_info()

            if self._model is None:
                interface_info = await self._dev.get_interface_information()
                self._model = interface_info.modelName

            volumes = await self._dev.get_volume_information()
            if not volumes:
                _LOGGER.error("Got no volume controls, bailing out")
                self._attr_available = False
                return

            if len(volumes) > 1:
                _LOGGER.debug("Got %s volume controls, using the first one", volumes)

            volume = volumes[0]
            _LOGGER.debug("Current volume: %s", volume)

            self._volume_max = volume.maxVolume
            self._volume_min = volume.minVolume
            self._volume = volume.volume
            self._volume_control = volume
            if self._volume_max:
                self._attr_volume_step = 1 / self._volume_max
            self._attr_is_volume_muted = self._volume_control.is_muted

            status = await self._dev.get_power()
            self._state = status.status
            _LOGGER.debug("Got state: %s", status)

            inputs = await self._dev.get_inputs()
            _LOGGER.debug("Got ins: %s", inputs)

            self._sources = OrderedDict()
            for input_ in inputs:
                self._sources[input_.uri] = input_
                if input_.active:
                    self._active_source = input_

            _LOGGER.debug("Active source: %s", self._active_source)

            (
                self._active_sound_mode,
                self._sound_modes,
            ) = await self._get_sound_modes_info()

            self._attr_available = True

        except SongpalException as ex:
            _LOGGER.error("Unable to update: %s", ex)
            self._attr_available = False