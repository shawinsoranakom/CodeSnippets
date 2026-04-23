def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        if self.coordinator.data.state.standby:
            return MediaPlayerState.OFF

        if self.coordinator.data.app is None:
            return None

        if (
            self.coordinator.data.app.name in {"Power Saver", "Roku"}
            or self.coordinator.data.app.screensaver
        ):
            return MediaPlayerState.IDLE

        if self.coordinator.data.media:
            if self.coordinator.data.media.paused:
                return MediaPlayerState.PAUSED
            return MediaPlayerState.PLAYING

        if self.coordinator.data.app.name:
            return MediaPlayerState.ON

        return None