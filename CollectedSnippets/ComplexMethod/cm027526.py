def _determine_features(self) -> MediaPlayerEntityFeature:
        flags = (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.VOLUME_MUTE
        )
        if self.supports_capability(Capability.MEDIA_PLAYBACK):
            playback_commands = self.get_attribute_value(
                Capability.MEDIA_PLAYBACK, Attribute.SUPPORTED_PLAYBACK_COMMANDS
            )
            if "play" in playback_commands:
                flags |= MediaPlayerEntityFeature.PLAY
            if "pause" in playback_commands:
                flags |= MediaPlayerEntityFeature.PAUSE
            if "stop" in playback_commands:
                flags |= MediaPlayerEntityFeature.STOP
            if "rewind" in playback_commands:
                flags |= MediaPlayerEntityFeature.PREVIOUS_TRACK
            if "fastForward" in playback_commands:
                flags |= MediaPlayerEntityFeature.NEXT_TRACK
        if self.supports_capability(Capability.SWITCH):
            flags |= (
                MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
            )
        if self.supports_capability(Capability.MEDIA_INPUT_SOURCE):
            flags |= MediaPlayerEntityFeature.SELECT_SOURCE
        if self.supports_capability(Capability.MEDIA_PLAYBACK_SHUFFLE):
            flags |= MediaPlayerEntityFeature.SHUFFLE_SET
        if self.supports_capability(Capability.MEDIA_PLAYBACK_REPEAT):
            flags |= MediaPlayerEntityFeature.REPEAT_SET
        return flags