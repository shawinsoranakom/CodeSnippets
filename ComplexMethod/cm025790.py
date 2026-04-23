async def async_update(self) -> None:
        """Get the latest date and update device state."""
        afsapi = self.fs_device
        try:
            if await afsapi.get_power():
                status = await afsapi.get_play_status()
                self._attr_state = {
                    PlayState.IDLE: MediaPlayerState.IDLE,
                    PlayState.BUFFERING: MediaPlayerState.BUFFERING,
                    PlayState.PLAYING: MediaPlayerState.PLAYING,
                    PlayState.PAUSED: MediaPlayerState.PAUSED,
                    PlayState.REBUFFERING: MediaPlayerState.BUFFERING,
                    PlayState.STOPPED: MediaPlayerState.IDLE,
                }.get(status, MediaPlayerState.IDLE)
            else:
                self._attr_state = MediaPlayerState.OFF
        except FSConnectionError:
            if self._attr_available:
                _LOGGER.warning(
                    "Could not connect to %s. Did it go offline?",
                    self.name or afsapi.webfsapi_endpoint,
                )
                self._attr_available = False

            # Device is not available, stop the update
            return

        if not self._attr_available:
            _LOGGER.warning(
                "Reconnected to %s",
                self.name or afsapi.webfsapi_endpoint,
            )

            self._attr_available = True

        if not self._attr_source_list:
            self.__modes_by_label = {
                (mode.label or mode.id): mode.key for mode in await afsapi.get_modes()
            }
            self._attr_source_list = list(self.__modes_by_label)

        try:
            self.__play_caps = await afsapi.get_play_caps()
        except FSNotImplementedError:
            self.__play_caps = self._FALLBACK_PLAY_CAPS

        if self.__play_caps & (PlayCaps.REPEAT | PlayCaps.REPEAT_ONE):
            try:
                repeat_mode = await afsapi.get_play_repeat()
            except FSNotImplementedError:
                self._attr_repeat = RepeatMode.OFF
            else:
                self._attr_repeat = {
                    PlayRepeatMode.OFF: RepeatMode.OFF,
                    PlayRepeatMode.REPEAT_ALL: RepeatMode.ALL,
                    PlayRepeatMode.REPEAT_ONE: RepeatMode.ONE,
                }.get(repeat_mode, RepeatMode.OFF)
        else:
            self._attr_repeat = RepeatMode.OFF

        if self.__play_caps & PlayCaps.SHUFFLE:
            try:
                self._attr_shuffle = bool(await afsapi.get_play_shuffle())
            except FSNotImplementedError:
                self._attr_shuffle = False
        else:
            self._attr_shuffle = False

        if not self._attr_sound_mode_list and self._supports_sound_mode:
            try:
                equalisers = await afsapi.get_equalisers()
            except FSNotImplementedError:
                self._supports_sound_mode = False
            else:
                self.__sound_modes_by_label = {
                    sound_mode.label: sound_mode.key for sound_mode in equalisers
                }
                self._attr_sound_mode_list = list(self.__sound_modes_by_label)

        # The API seems to include 'zero' in the number of steps (e.g. if the range is
        # 0-40 then get_volume_steps returns 41) subtract one to get the max volume.
        # If call to get_volume fails set to 0 and try again next time.
        if not self._max_volume:
            self._max_volume = int(await afsapi.get_volume_steps() or 1) - 1

        if self._attr_state != MediaPlayerState.OFF:
            info_name = await afsapi.get_play_name()
            info_text = await afsapi.get_play_text()

            self._attr_media_title = " - ".join(filter(None, [info_name, info_text]))
            self._attr_media_artist = await afsapi.get_play_artist()
            self._attr_media_album_name = await afsapi.get_play_album()

            radio_mode = await afsapi.get_mode()
            self._attr_source = radio_mode.label if radio_mode is not None else None

            self._attr_is_volume_muted = await afsapi.get_mute()
            self._attr_media_image_url = await afsapi.get_play_graphic()

            if self.__play_caps and self.__play_caps & PlayCaps.SEEK:
                position_ms = await afsapi.get_play_position()
                duration_ms = await afsapi.get_play_duration()
                self._attr_media_position = (
                    position_ms // 1000 if position_ms is not None else None
                )
                self._attr_media_duration = (
                    duration_ms // 1000 if duration_ms is not None else None
                )
                self._attr_media_position_updated_at = dt_util.utcnow()
            else:
                self._attr_media_position = None
                self._attr_media_duration = None
                self._attr_media_position_updated_at = None

            if self._supports_sound_mode:
                try:
                    eq_preset = await afsapi.get_eq_preset()
                except FSNotImplementedError:
                    self._supports_sound_mode = False
                else:
                    self._attr_sound_mode = (
                        eq_preset.label if eq_preset is not None else None
                    )

            volume = await self.fs_device.get_volume()

            # Prevent division by zero if max_volume not known yet
            self._attr_volume_level = float(volume or 0) / (self._max_volume or 1)
        else:
            self._attr_media_title = None
            self._attr_media_artist = None
            self._attr_media_album_name = None

            self._attr_source = None

            self._attr_is_volume_muted = None
            self._attr_media_image_url = None
            self._attr_sound_mode = None
            self._attr_media_position = None
            self._attr_media_duration = None
            self._attr_media_position_updated_at = None

            self._attr_volume_level = None