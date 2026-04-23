async def _async_update_data(self) -> SpotifyCoordinatorData:
        self.update_interval = UPDATE_INTERVAL
        try:
            current = await self.client.get_playback()
        except SpotifyConnectionError as err:
            raise UpdateFailed("Error communicating with Spotify API") from err
        if not current:
            return SpotifyCoordinatorData(
                current_playback=None,
                position_updated_at=None,
                playlist=None,
            )
        # Record the last updated time, because Spotify's timestamp property is unreliable
        # and doesn't actually return the fetch time as is mentioned in the API description
        position_updated_at = dt_util.utcnow()

        dj_playlist = False
        if (context := current.context) is not None:
            dj_playlist = context.uri == SPOTIFY_DJ_PLAYLIST_URI
            if not (
                context.uri
                in (
                    self._checked_playlist_id,
                    SPOTIFY_DJ_PLAYLIST_URI,
                )
                or (self._playlist is None and context.uri == self._checked_playlist_id)
            ):
                self._checked_playlist_id = context.uri
                self._playlist = None
                if context.context_type == ContextType.PLAYLIST:
                    # Make sure any playlist lookups don't break the current
                    # playback state update
                    try:
                        self._playlist = await self.client.get_playlist(context.uri)
                    except SpotifyNotFoundError:
                        _LOGGER.debug(
                            "Spotify playlist '%s' not found. "
                            "Most likely a Spotify-created playlist",
                            context.uri,
                        )
                        self._playlist = None
                    except SpotifyConnectionError:
                        _LOGGER.debug(
                            "Unable to load spotify playlist '%s'. "
                            "Continuing without playlist data",
                            context.uri,
                        )
                        self._playlist = None
                        self._checked_playlist_id = None
        if current.is_playing and current.progress_ms is not None:
            assert current.item is not None
            time_left = timedelta(
                milliseconds=current.item.duration_ms - current.progress_ms
            )
            if time_left < UPDATE_INTERVAL:
                self.update_interval = time_left + timedelta(seconds=1)
        return SpotifyCoordinatorData(
            current_playback=current,
            position_updated_at=position_updated_at,
            playlist=self._playlist,
            dj_playlist=dj_playlist,
        )