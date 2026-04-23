def _update_from_session_data(self) -> None:
        """Process session data to update entity properties."""
        state = None
        media_content_type = None
        media_content_id = None
        media_title = None
        media_series_title = None
        media_season = None
        media_episode = None
        media_album_name = None
        media_album_artist = None
        media_artist = None
        media_track = None
        media_duration = None
        media_position = None
        media_position_updated = None
        volume_muted = False
        volume_level = None

        if self.available:
            state = MediaPlayerState.IDLE
            media_position_updated = (
                parse_datetime(self.session_data["LastPlaybackCheckIn"])
                if self.now_playing
                else None
            )

        if self.now_playing is not None:
            state = MediaPlayerState.PLAYING
            media_content_type = CONTENT_TYPE_MAP.get(self.now_playing["Type"], None)
            media_content_id = self.now_playing["Id"]
            media_title = self.now_playing["Name"]

            if "RunTimeTicks" in self.now_playing:
                media_duration = int(self.now_playing["RunTimeTicks"] / 10000000)

            if media_content_type == MediaType.EPISODE:
                media_content_type = MediaType.TVSHOW
                media_series_title = self.now_playing.get("SeriesName")
                media_season = self.now_playing.get("ParentIndexNumber")
                media_episode = self.now_playing.get("IndexNumber")
            elif media_content_type == MediaType.MUSIC:
                media_album_name = self.now_playing.get("Album")
                media_album_artist = self.now_playing.get("AlbumArtist")
                media_track = self.now_playing.get("IndexNumber")
                if media_artists := self.now_playing.get("Artists"):
                    media_artist = str(media_artists[0])

        if self.play_state is not None:
            if self.play_state.get("IsPaused"):
                state = MediaPlayerState.PAUSED

            media_position = (
                int(self.play_state["PositionTicks"] / 10000000)
                if "PositionTicks" in self.play_state
                else None
            )
            volume_muted = bool(self.play_state.get("IsMuted", False))
            volume_level = (
                float(self.play_state["VolumeLevel"] / 100)
                if "VolumeLevel" in self.play_state
                else None
            )

        self._attr_state = state
        self._attr_is_volume_muted = volume_muted
        # Only update volume_level if the API provides it, otherwise preserve current value
        if volume_level is not None:
            self._attr_volume_level = volume_level
        self._attr_media_content_type = media_content_type
        self._attr_media_content_id = media_content_id
        self._attr_media_title = media_title
        self._attr_media_series_title = media_series_title
        self._attr_media_season = media_season
        self._attr_media_episode = media_episode
        self._attr_media_album_name = media_album_name
        self._attr_media_album_artist = media_album_artist
        self._attr_media_artist = media_artist
        self._attr_media_track = media_track
        self._attr_media_duration = media_duration
        self._attr_media_position = media_position
        self._attr_media_position_updated_at = media_position_updated