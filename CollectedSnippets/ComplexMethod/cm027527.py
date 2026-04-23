def state(self) -> MediaPlayerState | None:
        """State of the media player."""
        if self.supports_capability(Capability.SWITCH):
            if not self.supports_capability(Capability.MEDIA_PLAYBACK):
                if (
                    self.get_attribute_value(Capability.SWITCH, Attribute.SWITCH)
                    == "on"
                ):
                    return MediaPlayerState.ON
                return MediaPlayerState.OFF
            if self.get_attribute_value(Capability.SWITCH, Attribute.SWITCH) == "on":
                if (
                    self.source is not None
                    and self.source in CONTROLLABLE_SOURCES
                    and self.get_attribute_value(
                        Capability.MEDIA_PLAYBACK, Attribute.PLAYBACK_STATUS
                    )
                    in VALUE_TO_STATE
                ):
                    return VALUE_TO_STATE[
                        self.get_attribute_value(
                            Capability.MEDIA_PLAYBACK, Attribute.PLAYBACK_STATUS
                        )
                    ]
                return MediaPlayerState.ON
            return MediaPlayerState.OFF
        return VALUE_TO_STATE[
            self.get_attribute_value(
                Capability.MEDIA_PLAYBACK, Attribute.PLAYBACK_STATUS
            )
        ]