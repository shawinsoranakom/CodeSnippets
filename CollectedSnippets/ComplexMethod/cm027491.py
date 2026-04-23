def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        features = MediaPlayerEntityFeature.TURN_OFF | MediaPlayerEntityFeature.TURN_ON

        if self.service.has(CharacteristicsTypes.ACTIVE_IDENTIFIER):
            features |= MediaPlayerEntityFeature.SELECT_SOURCE

        if self.service.has(CharacteristicsTypes.TARGET_MEDIA_STATE):
            if TargetMediaStateValues.PAUSE in self.supported_media_states:
                features |= MediaPlayerEntityFeature.PAUSE

            if TargetMediaStateValues.PLAY in self.supported_media_states:
                features |= MediaPlayerEntityFeature.PLAY

            if TargetMediaStateValues.STOP in self.supported_media_states:
                features |= MediaPlayerEntityFeature.STOP

        if (
            self.service.has(CharacteristicsTypes.REMOTE_KEY)
            and RemoteKeyValues.PLAY_PAUSE in self.supported_remote_keys
        ):
            features |= MediaPlayerEntityFeature.PAUSE | MediaPlayerEntityFeature.PLAY

        return features