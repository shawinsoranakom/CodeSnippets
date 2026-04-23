async def async_update(self) -> None:
        """Get the latest details from the device."""
        if not self.available:
            try:
                await self._vlc.connect()
            except ConnectError as err:
                LOGGER.debug("Connection error: %s", err)
                return

            try:
                await self._vlc.login()
            except AuthError:
                LOGGER.debug("Failed to login to VLC")
                self.hass.async_create_task(
                    self.hass.config_entries.async_reload(self._config_entry.entry_id)
                )
                return

            self._attr_state = MediaPlayerState.IDLE
            self._attr_available = True
            LOGGER.debug("Connected to vlc host: %s", self._vlc.host)

        status = await self._vlc.status()
        LOGGER.debug("Status: %s", status)

        self._attr_volume_level = status.audio_volume / MAX_VOLUME
        state = status.state
        if state == "playing":
            self._attr_state = MediaPlayerState.PLAYING
        elif state == "paused":
            self._attr_state = MediaPlayerState.PAUSED
        else:
            self._attr_state = MediaPlayerState.IDLE

        if self._attr_state != MediaPlayerState.IDLE:
            self._attr_media_duration = (await self._vlc.get_length()).length
            time_output = await self._vlc.get_time()
            vlc_position = time_output.time

            # Check if current position is stale.
            if vlc_position != self.media_position:
                self._attr_media_position_updated_at = dt_util.utcnow()
                self._attr_media_position = vlc_position

        info = await self._vlc.info()
        data = info.data
        LOGGER.debug("Info data: %s", data)

        self._attr_media_album_name = _get_str(data.get("data", {}), "album")
        self._attr_media_artist = _get_str(data.get("data", {}), "artist")
        self._attr_media_title = _get_str(data.get("data", {}), "title")
        now_playing = _get_str(data.get("data", {}), "now_playing")

        # Many radio streams put artist/title/album in now_playing and title is the station name.
        if now_playing:
            if not self.media_artist:
                self._attr_media_artist = self._attr_media_title
            self._attr_media_title = now_playing

        if self.media_title:
            return

        # Fall back to filename.
        if data_info := data.get("data"):
            media_title = _get_str(data_info, "filename")

            # Strip out auth signatures if streaming local media
            if media_title and (pos := media_title.find("?authSig=")) != -1:
                self._attr_media_title = media_title[:pos]
            else:
                self._attr_media_title = media_title