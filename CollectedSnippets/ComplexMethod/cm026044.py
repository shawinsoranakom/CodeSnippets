def __init__(
        self,
        manager: ReceiverManager,
        zone: Zone,
        *,
        volume_resolution: VolumeResolution,
        max_volume: float,
        sources: dict[InputSource, str],
        sound_modes: dict[ListeningMode, str],
    ) -> None:
        """Initialize the Onkyo Receiver."""
        self._manager = manager
        self._zone = zone

        name = manager.info.model_name
        identifier = manager.info.identifier
        self._attr_name = f"{name}{' ' + ZONES[zone] if zone != Zone.MAIN else ''}"
        self._attr_unique_id = f"{identifier}_{zone.value}"

        self._volume_resolution = volume_resolution
        self._max_volume = max_volume

        zone_sources = InputSource.for_zone(zone)
        self._source_mapping = {
            key: value for key, value in sources.items() if key in zone_sources
        }
        self._rev_source_mapping = {
            value: key for key, value in self._source_mapping.items()
        }

        zone_sound_modes = ListeningMode.for_zone(zone)
        self._sound_mode_mapping = {
            key: value for key, value in sound_modes.items() if key in zone_sound_modes
        }
        self._rev_sound_mode_mapping = {
            value: key for key, value in self._sound_mode_mapping.items()
        }

        self._hdmi_output_mapping = LEGACY_HDMI_OUTPUT_MAPPING
        self._rev_hdmi_output_mapping = LEGACY_REV_HDMI_OUTPUT_MAPPING

        self._attr_source_list = list(self._rev_source_mapping)
        self._attr_sound_mode_list = list(self._rev_sound_mode_mapping)

        self._attr_supported_features = SUPPORTED_FEATURES_BASE
        if zone == Zone.MAIN:
            self._attr_supported_features |= SUPPORTED_FEATURES_VOLUME
            self._supports_volume = True
            self._attr_supported_features |= MediaPlayerEntityFeature.SELECT_SOUND_MODE
            self._supports_sound_mode = True
        elif Code.get_from_kind_zone(Kind.LISTENING_MODE, zone) is not None:
            # To be detected later:
            self._supports_sound_mode = False

        self._attr_extra_state_attributes = {}