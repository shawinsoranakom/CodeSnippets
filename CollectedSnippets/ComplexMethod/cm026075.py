def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        if self.manager.is_connecting:
            return None
        if self.atv is None:
            return MediaPlayerState.OFF
        if (
            self._is_feature_available(FeatureName.PowerState)
            and self.atv.power.power_state == PowerState.Off
        ):
            return MediaPlayerState.OFF
        if self._playing:
            state = self._playing.device_state
            if state in (DeviceState.Idle, DeviceState.Loading):
                return MediaPlayerState.IDLE
            if state == DeviceState.Playing:
                return MediaPlayerState.PLAYING
            if state in (DeviceState.Paused, DeviceState.Seeking, DeviceState.Stopped):
                return MediaPlayerState.PAUSED
            return MediaPlayerState.IDLE  # Bad or unknown state?
        return None