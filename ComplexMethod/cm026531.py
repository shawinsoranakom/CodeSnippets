def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        support = (
            MediaPlayerEntityFeature.PLAY_MEDIA
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.TURN_ON
        )
        media_status = self._media_status()[0]

        if (
            self.cast_status
            and self.cast_status.volume_control_type != VOLUME_CONTROL_TYPE_FIXED
        ):
            support |= (
                MediaPlayerEntityFeature.VOLUME_MUTE
                | MediaPlayerEntityFeature.VOLUME_SET
            )

        if media_status and self.app_id != CAST_APP_ID_HOMEASSISTANT_LOVELACE:
            support |= (
                MediaPlayerEntityFeature.PAUSE
                | MediaPlayerEntityFeature.PLAY
                | MediaPlayerEntityFeature.STOP
            )
            if media_status.supports_queue_next:
                support |= (
                    MediaPlayerEntityFeature.PREVIOUS_TRACK
                    | MediaPlayerEntityFeature.NEXT_TRACK
                )
            if media_status.supports_seek:
                support |= MediaPlayerEntityFeature.SEEK

        if "media_source" in self.hass.config.components:
            support |= MediaPlayerEntityFeature.BROWSE_MEDIA

        return support