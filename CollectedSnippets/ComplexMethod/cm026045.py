def process_update(self, message: status.Known) -> None:
        """Process update."""
        match message:
            case status.Power(param=status.Power.Param.ON):
                if self.state != MediaPlayerState.ON:
                    self._query_state_delayed()
                self._attr_state = MediaPlayerState.ON
            case status.Power(param=status.Power.Param.STANDBY):
                self._attr_state = MediaPlayerState.OFF

            case status.Volume(param=volume):
                if not self._supports_volume:
                    self._attr_supported_features |= SUPPORTED_FEATURES_VOLUME
                    self._supports_volume = True
                # AMP_VOL / (VOL_RESOLUTION * (MAX_VOL / 100))
                volume_level: float = volume / (
                    self._volume_resolution * self._max_volume / 100
                )
                self._attr_volume_level = min(1, volume_level)

            case status.Muting(param=muting):
                self._attr_is_volume_muted = bool(muting == status.Muting.Param.ON)

            case status.InputSource(param=source):
                if source in self._source_mapping:
                    self._attr_source = self._source_mapping[source]
                else:
                    source_meaning = get_meaning(source)
                    _LOGGER.warning(
                        'Input source "%s" for entity: %s is not in the list. Check integration options',
                        source_meaning,
                        self.entity_id,
                    )
                    self._attr_source = source_meaning

                self._query_av_info_delayed()

            case status.ListeningMode(param=sound_mode):
                if not self._supports_sound_mode:
                    self._attr_supported_features |= (
                        MediaPlayerEntityFeature.SELECT_SOUND_MODE
                    )
                    self._supports_sound_mode = True

                if sound_mode in self._sound_mode_mapping:
                    self._attr_sound_mode = self._sound_mode_mapping[sound_mode]
                else:
                    sound_mode_meaning = get_meaning(sound_mode)
                    _LOGGER.warning(
                        'Listening mode "%s" for entity: %s is not in the list. Check integration options',
                        sound_mode_meaning,
                        self.entity_id,
                    )
                    self._attr_sound_mode = sound_mode_meaning

                self._query_av_info_delayed()

            case status.HDMIOutput(param=hdmi_output):
                self._attr_extra_state_attributes[ATTR_VIDEO_OUT] = (
                    self._hdmi_output_mapping[hdmi_output]
                )
                self._query_av_info_delayed()

            case status.TunerPreset(param=preset):
                self._attr_extra_state_attributes[ATTR_PRESET] = preset

            case status.AudioInformation():
                self._supports_audio_info = True
                audio_information = {}
                for item in AUDIO_INFORMATION_MAPPING:
                    item_value = getattr(message, item)
                    if item_value is not None:
                        audio_information[item] = item_value
                self._attr_extra_state_attributes[ATTR_AUDIO_INFORMATION] = (
                    audio_information
                )

            case status.VideoInformation():
                self._supports_video_info = True
                video_information = {}
                for item in VIDEO_INFORMATION_MAPPING:
                    item_value = getattr(message, item)
                    if item_value is not None:
                        video_information[item] = item_value
                self._attr_extra_state_attributes[ATTR_VIDEO_INFORMATION] = (
                    video_information
                )

            case status.FLDisplay():
                self._query_av_info_delayed()

            case status.NotAvailable(kind=Kind.AUDIO_INFORMATION):
                # Not available right now, but still supported
                self._supports_audio_info = True

            case status.NotAvailable(kind=Kind.VIDEO_INFORMATION):
                # Not available right now, but still supported
                self._supports_video_info = True

        self.async_write_ha_state()