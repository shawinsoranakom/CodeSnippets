async def _async_update_data(self) -> VizioDeviceData:
        """Fetch all device data."""
        is_on = await self.device.get_power_state(log_api_exception=False)

        if is_on is None:
            raise UpdateFailed(
                f"Unable to connect to {self.config_entry.data[CONF_HOST]}"
            )

        if not is_on:
            return VizioDeviceData(is_on=False)

        # Device is on - fetch all data
        audio_settings = await self.device.get_all_settings(
            VIZIO_AUDIO_SETTINGS, log_api_exception=False
        )

        sound_mode_list = None
        if audio_settings and VIZIO_SOUND_MODE in audio_settings:
            sound_mode_list = await self.device.get_setting_options(
                VIZIO_AUDIO_SETTINGS, VIZIO_SOUND_MODE, log_api_exception=False
            )

        current_input = await self.device.get_current_input(log_api_exception=False)
        input_list = await self.device.get_inputs_list(log_api_exception=False)

        current_app_config = None
        # Only attempt to fetch app config if the device is a TV and supports apps
        if (
            self.config_entry.data[CONF_DEVICE_CLASS] == MediaPlayerDeviceClass.TV
            and input_list
            and any(input_item.name in INPUT_APPS for input_item in input_list)
        ):
            current_app_config = await self.device.get_current_app_config(
                log_api_exception=False
            )

        return VizioDeviceData(
            is_on=True,
            audio_settings=audio_settings,
            sound_mode_list=sound_mode_list,
            current_input=current_input,
            input_list=input_list,
            current_app_config=current_app_config,
        )