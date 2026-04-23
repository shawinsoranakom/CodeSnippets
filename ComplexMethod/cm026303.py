def _async_update_device_from_protect(self, device: ProtectDeviceType) -> None:
        super()._async_update_device_from_protect(device)
        updated_device = self.device
        speaker_settings = updated_device.speaker_settings
        volume = (
            speaker_settings.speaker_volume
            if speaker_settings.speaker_volume is not None
            else speaker_settings.volume
        )
        self._attr_volume_level = float(volume / 100)

        if (
            updated_device.talkback_stream is not None
            and updated_device.talkback_stream.is_running
        ):
            self._attr_state = MediaPlayerState.PLAYING
        else:
            self._attr_state = MediaPlayerState.IDLE

        is_connected = self.data.last_update_success and (
            updated_device.state is StateType.CONNECTED
            or (not updated_device.is_adopted_by_us and updated_device.can_adopt)
        )
        self._attr_available = is_connected and updated_device.feature_flags.has_speaker