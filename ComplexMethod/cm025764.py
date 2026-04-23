def _async_update_attrs(self) -> None:
        """Update entity attributes."""
        self._volume_max = (
            self.get("vehicle_state_media_info_audio_volume_max") or VOLUME_MAX
        )
        self._attr_state = STATES.get(
            self.get("vehicle_state_media_info_media_playback_status") or "Off",
        )
        self._attr_volume_step = (
            1.0
            / self._volume_max
            / (
                self.get("vehicle_state_media_info_audio_volume_increment")
                or VOLUME_STEP
            )
        )

        if volume := self.get("vehicle_state_media_info_audio_volume"):
            self._attr_volume_level = volume / self._volume_max
        else:
            self._attr_volume_level = None

        if duration := self.get("vehicle_state_media_info_now_playing_duration"):
            self._attr_media_duration = duration / 1000
        else:
            self._attr_media_duration = None

        if duration and (
            position := self.get("vehicle_state_media_info_now_playing_elapsed")
        ):
            self._attr_media_position = position / 1000
        else:
            self._attr_media_position = None

        self._attr_media_title = self.get("vehicle_state_media_info_now_playing_title")
        self._attr_media_artist = self.get(
            "vehicle_state_media_info_now_playing_artist"
        )
        self._attr_media_album_name = self.get(
            "vehicle_state_media_info_now_playing_album"
        )
        self._attr_media_playlist = self.get(
            "vehicle_state_media_info_now_playing_station"
        )
        self._attr_source = self.get("vehicle_state_media_info_now_playing_source")