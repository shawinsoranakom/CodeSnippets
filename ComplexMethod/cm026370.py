def update_state(self):
        """Update the power state and player state."""

        new_state = ""
        # power state from source control (if supported)
        if "source_controls" in self.player_data:
            for source in self.player_data["source_controls"]:
                if source["supports_standby"] and source["status"] != "indeterminate":
                    self._supports_standby = True
                    if source["status"] in ["standby", "deselected"]:
                        new_state = MediaPlayerState.OFF
                    break
        # determine player state
        if not new_state:
            if (
                self.player_data["state"] == "playing"
                or self.player_data["state"] == "loading"
            ):
                new_state = MediaPlayerState.PLAYING
            elif self.player_data["state"] == "stopped":
                new_state = MediaPlayerState.IDLE
            elif self.player_data["state"] == "paused":
                new_state = MediaPlayerState.PAUSED
            else:
                new_state = MediaPlayerState.IDLE
        self._attr_state = new_state
        self._attr_unique_id = self.player_data["dev_id"]
        self._zone_id = self.player_data["zone_id"]
        self._output_id = self.player_data["output_id"]
        self._attr_repeat = REPEAT_MODE_MAPPING_TO_HA.get(
            self.player_data["settings"]["loop"]
        )
        self._attr_shuffle = self.player_data["settings"]["shuffle"]
        self._attr_name = self.player_data["display_name"]

        volume = RoonDevice._parse_volume(self.player_data)
        self._attr_is_volume_muted = volume["muted"]
        self._attr_volume_step = volume["step"]
        self._attr_volume_level = volume["level"]
        self._volume_fixed = volume["fixed"]
        self._volume_incremental = volume["incremental"]
        if not self._volume_fixed:
            self._attr_supported_features = (
                self._attr_supported_features | MediaPlayerEntityFeature.VOLUME_STEP
            )
            if not self._volume_incremental:
                self._attr_supported_features = (
                    self._attr_supported_features | MediaPlayerEntityFeature.VOLUME_SET
                )

        now_playing = self._parse_now_playing(self.player_data)
        self._attr_media_title = now_playing["title"]
        self._attr_media_artist = now_playing["artist"]
        self._attr_media_album_name = now_playing["album"]
        self._attr_media_position = now_playing["position"]
        self._attr_media_duration = now_playing["duration"]
        self._attr_media_image_url = now_playing["image"]