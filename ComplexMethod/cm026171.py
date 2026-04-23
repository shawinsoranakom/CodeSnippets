def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        supported_features = MUSIC_PLAYER_BASE_SUPPORT
        zone = self.coordinator.data.zones[self._zone_id]

        if ZoneFeature.POWER in zone.features:
            supported_features |= (
                MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
            )
        if ZoneFeature.VOLUME in zone.features:
            supported_features |= (
                MediaPlayerEntityFeature.VOLUME_SET
                | MediaPlayerEntityFeature.VOLUME_STEP
            )
        if ZoneFeature.MUTE in zone.features:
            supported_features |= MediaPlayerEntityFeature.VOLUME_MUTE

        if self._is_netusb or self._is_tuner:
            supported_features |= MediaPlayerEntityFeature.PREVIOUS_TRACK
            supported_features |= MediaPlayerEntityFeature.NEXT_TRACK

        if self._is_netusb:
            supported_features |= MediaPlayerEntityFeature.PAUSE
            supported_features |= MediaPlayerEntityFeature.PLAY
            supported_features |= MediaPlayerEntityFeature.STOP

        if self.state != MediaPlayerState.OFF:
            supported_features |= MediaPlayerEntityFeature.BROWSE_MEDIA

        return supported_features