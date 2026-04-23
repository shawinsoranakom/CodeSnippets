def _async_update_from_player(self) -> None:
        """Update entity attributes from the shared player object."""
        if self._player.power is None:
            self._attr_state = None
        else:
            self._attr_state = (
                MediaPlayerState.ON if self._player.power else MediaPlayerState.OFF
            )

        source = self._player.input_source
        self._attr_source = INPUT_SOURCE_DENON_TO_HA.get(source) if source else None

        volume_min = self._player.volume_min
        volume_max = self._player.volume_max
        if volume_min is not None:
            self._volume_min = volume_min

            if volume_max is not None and volume_max > volume_min:
                self._volume_range = volume_max - volume_min

        volume = self._player.volume
        if volume is not None:
            self._attr_volume_level = (volume - self._volume_min) / self._volume_range
        else:
            self._attr_volume_level = None

        if self._is_main:
            self._attr_is_volume_muted = cast(MainPlayer, self._player).mute