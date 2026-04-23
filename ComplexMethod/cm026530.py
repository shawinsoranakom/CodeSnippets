def state(self) -> MediaPlayerState | None:
        """Return the state of the player."""
        if (chromecast := self._chromecast) is None or (
            cast_status := self.cast_status
        ) is None:
            # Not connected to any chromecast, or not yet got any status
            return None

        if (
            chromecast.cast_type == pychromecast.const.CAST_TYPE_CHROMECAST
            and not chromecast.ignore_cec
            and cast_status.is_active_input is False
        ):
            # The display interface for the device has been turned off or switched away
            return MediaPlayerState.OFF

        if self.app_id == CAST_APP_ID_HOMEASSISTANT_LOVELACE:
            # The lovelace app loops media to prevent timing out, don't show that
            return MediaPlayerState.PLAYING

        if (media_status := self._media_status()[0]) is not None:
            if media_status.player_state == MEDIA_PLAYER_STATE_PLAYING:
                return MediaPlayerState.PLAYING
            if media_status.player_state == MEDIA_PLAYER_STATE_BUFFERING:
                return MediaPlayerState.BUFFERING
            if media_status.player_is_paused:
                return MediaPlayerState.PAUSED
            if media_status.player_is_idle:
                return MediaPlayerState.IDLE

        if self.app_id in APP_IDS_UNRELIABLE_MEDIA_INFO:
            # Some apps don't report media status, show the player as playing
            return MediaPlayerState.PLAYING

        if self.app_id in (pychromecast.IDLE_APP_ID, None):
            # We have no active app or the home screen app. This is
            # same app as APP_BACKDROP.
            return MediaPlayerState.OFF

        return MediaPlayerState.IDLE