def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data

        # Handle device off
        if not data.is_on:
            self._attr_state = MediaPlayerState.OFF
            self._attr_volume_level = None
            self._attr_is_volume_muted = None
            self._attr_sound_mode = None
            self._attr_app_name = None
            self._current_input = None
            self._current_app_config = None
            super()._handle_coordinator_update()
            return

        # Device is on - apply coordinator data
        self._attr_state = MediaPlayerState.ON

        # Audio settings
        if data.audio_settings:
            self._attr_volume_level = (
                float(data.audio_settings[VIZIO_VOLUME]) / self._max_volume
            )
            if VIZIO_MUTE in data.audio_settings:
                self._attr_is_volume_muted = (
                    data.audio_settings[VIZIO_MUTE].lower() == VIZIO_MUTE_ON
                )
            else:
                self._attr_is_volume_muted = None
            if VIZIO_SOUND_MODE in data.audio_settings:
                self._attr_supported_features |= (
                    MediaPlayerEntityFeature.SELECT_SOUND_MODE
                )
                self._attr_sound_mode = data.audio_settings[VIZIO_SOUND_MODE]
                if not self._attr_sound_mode_list:
                    self._attr_sound_mode_list = data.sound_mode_list or []
            else:
                self._attr_supported_features &= (
                    ~MediaPlayerEntityFeature.SELECT_SOUND_MODE
                )

        # Input state
        if data.current_input:
            self._current_input = data.current_input
        if data.input_list:
            self._available_inputs = [i.name for i in data.input_list]

        # App state (TV only) - check if device supports apps
        if (
            self._attr_device_class == MediaPlayerDeviceClass.TV
            and self._available_inputs
            and any(app in self._available_inputs for app in INPUT_APPS)
        ):
            all_apps = self._all_apps or ()
            self._available_apps = self._apps_list([app["name"] for app in all_apps])
            self._current_app_config = data.current_app_config
            self._attr_app_name = find_app_name(
                self._current_app_config,
                [APP_HOME, *all_apps, *self._additional_app_configs],
            )
            if self._attr_app_name == NO_APP_RUNNING:
                self._attr_app_name = None

        super()._handle_coordinator_update()