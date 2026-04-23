def _update_states(self) -> None:
        """Update entity state attributes."""
        tv_state = self._client.tv_state
        self._update_sources()

        self._attr_state = (
            MediaPlayerState.ON if tv_state.is_on else MediaPlayerState.OFF
        )
        self._attr_is_volume_muted = cast(bool, tv_state.muted)

        self._attr_volume_level = None
        if tv_state.volume is not None:
            self._attr_volume_level = tv_state.volume / 100.0

        self._attr_source = self._current_source
        self._attr_source_list = sorted(self._source_list)

        self._attr_media_content_type = None
        if tv_state.current_app_id == LIVE_TV_APP_ID:
            self._attr_media_content_type = MediaType.CHANNEL

        self._attr_media_title = None
        if (tv_state.current_app_id == LIVE_TV_APP_ID) and (
            tv_state.current_channel is not None
        ):
            self._attr_media_title = cast(
                str, tv_state.current_channel.get("channelName")
            )

        self._attr_media_image_url = None
        if tv_state.current_app_id in tv_state.apps:
            icon: str = tv_state.apps[tv_state.current_app_id]["largeIcon"]
            if not icon.startswith("http"):
                icon = tv_state.apps[tv_state.current_app_id]["icon"]
            self._attr_media_image_url = icon

        if self.state != MediaPlayerState.OFF or not self._supported_features:
            supported = SUPPORT_WEBOSTV
            if tv_state.sound_output == "external_speaker":
                supported = supported | SUPPORT_WEBOSTV_VOLUME
            elif tv_state.sound_output != "lineout":
                supported = (
                    supported
                    | SUPPORT_WEBOSTV_VOLUME
                    | MediaPlayerEntityFeature.VOLUME_SET
                )

            self._supported_features = supported

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, cast(str, self.unique_id))},
            manufacturer="LG",
            name=self._device_name,
        )

        self._attr_assumed_state = True
        if tv_state.is_on and tv_state.media_state:
            self._attr_assumed_state = False
            for entry in tv_state.media_state:
                if entry.get("playState") == "playing":
                    self._attr_state = MediaPlayerState.PLAYING
                elif entry.get("playState") == "paused":
                    self._attr_state = MediaPlayerState.PAUSED
                elif entry.get("playState") == "unloaded":
                    self._attr_state = MediaPlayerState.IDLE

        tv_info = self._client.tv_info
        if self.state != MediaPlayerState.OFF:
            maj_v = tv_info.software.get("major_ver")
            min_v = tv_info.software.get("minor_ver")
            if maj_v and min_v:
                self._attr_device_info["sw_version"] = f"{maj_v}.{min_v}"

            if model := tv_info.system.get("modelName"):
                self._attr_device_info["model"] = model

            if serial_number := tv_info.system.get("serialNumber"):
                self._attr_device_info["serial_number"] = serial_number

        self._attr_extra_state_attributes = {}
        if tv_state.sound_output is not None or self.state != MediaPlayerState.OFF:
            self._attr_extra_state_attributes = {
                ATTR_SOUND_OUTPUT: tv_state.sound_output
            }