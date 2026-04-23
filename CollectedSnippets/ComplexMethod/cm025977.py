def async_get_current_source(
        self, now_playing_media: HeosNowPlayingMedia
    ) -> str | None:
        """Determine current source from now playing media (either input source or favorite)."""
        # Try matching input source
        if now_playing_media.source_id == const.MUSIC_SOURCE_AUX_INPUT:
            # If playing a remote input, name will match station
            for input_source in self._inputs:
                if input_source.name == now_playing_media.station:
                    return input_source.name
            # If playing a local input, match media_id. This needs to be a second loop as media_id
            # will match both local and remote inputs, so prioritize remote match by name first.
            for input_source in self._inputs:
                if input_source.media_id == now_playing_media.media_id:
                    return input_source.name
        # Try matching favorite
        if now_playing_media.type == MediaType.STATION:
            # Some stations match on name:station, others match on media_id:album_id
            for favorite in self._favorites.values():
                if (
                    favorite.name == now_playing_media.station
                    or favorite.media_id == now_playing_media.album_id
                ):
                    return favorite.name
        return None