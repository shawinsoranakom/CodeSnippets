def _update_playinfo(self, data: dict[str, Any]) -> None:
        """Update the player info."""
        if "i_stream_type" in data:
            if self._stream_type != data["i_stream_type"]:
                self._stream_type = data["i_stream_type"]
                # Ask device for current play info when stream type changed.
                self._device.get_play()
            if data["i_stream_type"] == 0:
                # If the stream type is 0 (aka the soundbar is used as an actual soundbar)
                # the last track info should be cleared and the state should only be on or off,
                # as all playing/paused are not applicable in this mode
                self._attr_media_image_url = None
                self._attr_media_artist = None
                self._attr_media_title = None
                if self._device_on:
                    self._attr_state = MediaPlayerState.ON
                else:
                    self._attr_state = MediaPlayerState.OFF
        if "i_play_ctrl" in data:
            if self._device_on and self._stream_type != 0:
                if data["i_play_ctrl"] == 0:
                    self._attr_state = MediaPlayerState.PLAYING
                else:
                    self._attr_state = MediaPlayerState.PAUSED
        if "s_albumart" in data:
            self._attr_media_image_url = data["s_albumart"].strip() or None
        if "s_artist" in data:
            self._attr_media_artist = data["s_artist"].strip() or None
        if "s_title" in data:
            self._attr_media_title = data["s_title"].strip() or None
        if "b_support_play_ctrl" in data:
            self._support_play_control = data["b_support_play_ctrl"]