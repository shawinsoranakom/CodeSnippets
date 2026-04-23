def supported_features(self) -> MediaPlayerEntityFeature:
        """Return the currently supported features for this device."""
        features = self._BASE_SUPPORTED_FEATURES
        if self.__play_caps & (PlayCaps.PAUSE | PlayCaps.STOP):
            features |= MediaPlayerEntityFeature.PLAY
        if self.__play_caps & PlayCaps.PAUSE:
            features |= MediaPlayerEntityFeature.PAUSE
        if self.__play_caps & PlayCaps.STOP:
            features |= MediaPlayerEntityFeature.STOP
        if self.__play_caps & (
            PlayCaps.SKIP_PREVIOUS | PlayCaps.REWIND | PlayCaps.SKIP_BACKWARD
        ):
            features |= MediaPlayerEntityFeature.PREVIOUS_TRACK
        if self.__play_caps & (
            PlayCaps.SKIP_NEXT | PlayCaps.FAST_FORWARD | PlayCaps.SKIP_FORWARD
        ):
            features |= MediaPlayerEntityFeature.NEXT_TRACK
        if self.__play_caps & (PlayCaps.REPEAT | PlayCaps.REPEAT_ONE):
            features |= MediaPlayerEntityFeature.REPEAT_SET
        if self.__play_caps & PlayCaps.SHUFFLE:
            features |= MediaPlayerEntityFeature.SHUFFLE_SET
        if self.__play_caps & PlayCaps.SEEK:
            features |= MediaPlayerEntityFeature.SEEK
        if self._supports_sound_mode:
            features |= MediaPlayerEntityFeature.SELECT_SOUND_MODE

        return features