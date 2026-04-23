def update(self) -> None:
        """Retrieve the latest data from the Clementine Player."""
        try:
            client = self._client

            if client.state == "Playing":
                self._attr_state = MediaPlayerState.PLAYING
            elif client.state == "Paused":
                self._attr_state = MediaPlayerState.PAUSED
            elif client.state == "Disconnected":
                self._attr_state = MediaPlayerState.OFF
            else:
                self._attr_state = MediaPlayerState.PAUSED

            if client.last_update and (time.time() - client.last_update > 40):
                self._attr_state = MediaPlayerState.OFF

            volume = float(client.volume) if client.volume else 0.0
            self._attr_volume_level = volume / 100.0
            if client.active_playlist_id in client.playlists:
                self._attr_source = client.playlists[client.active_playlist_id]["name"]
            else:
                self._attr_source = "Unknown"
            self._attr_source_list = [s["name"] for s in client.playlists.values()]

            if client.current_track:
                self._attr_media_title = client.current_track["title"]
                self._attr_media_artist = client.current_track["track_artist"]
                self._attr_media_album_name = client.current_track["track_album"]
                self._attr_media_image_hash = client.current_track["track_id"]
            else:
                self._attr_media_image_hash = None

        except Exception:
            self._attr_state = MediaPlayerState.OFF
            raise