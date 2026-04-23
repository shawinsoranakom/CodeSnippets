def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag of media commands that are supported."""
        if self.available is False:
            return MediaPlayerEntityFeature(0)

        if self.is_grouped and not self.is_leader:
            return (
                MediaPlayerEntityFeature.VOLUME_STEP
                | MediaPlayerEntityFeature.VOLUME_SET
                | MediaPlayerEntityFeature.VOLUME_MUTE
                | MediaPlayerEntityFeature.GROUPING
            )

        supported = (
            MediaPlayerEntityFeature.CLEAR_PLAYLIST
            | MediaPlayerEntityFeature.BROWSE_MEDIA
            | MediaPlayerEntityFeature.GROUPING
        )

        if not self._status.indexing:
            supported = (
                supported
                | MediaPlayerEntityFeature.PAUSE
                | MediaPlayerEntityFeature.PREVIOUS_TRACK
                | MediaPlayerEntityFeature.NEXT_TRACK
                | MediaPlayerEntityFeature.PLAY_MEDIA
                | MediaPlayerEntityFeature.STOP
                | MediaPlayerEntityFeature.PLAY
                | MediaPlayerEntityFeature.SELECT_SOURCE
                | MediaPlayerEntityFeature.SHUFFLE_SET
            )

        current_vol = self.volume_level
        if current_vol is not None and current_vol >= 0:
            supported = (
                supported
                | MediaPlayerEntityFeature.VOLUME_STEP
                | MediaPlayerEntityFeature.VOLUME_SET
                | MediaPlayerEntityFeature.VOLUME_MUTE
            )

        if self._status.can_seek:
            supported = supported | MediaPlayerEntityFeature.SEEK

        return supported