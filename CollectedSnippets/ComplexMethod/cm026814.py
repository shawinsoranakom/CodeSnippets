def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize a Television Media Player accessory object."""
        super().__init__(
            MediaPlayerEntityFeature.SELECT_SOURCE,
            ATTR_INPUT_SOURCE,
            ATTR_INPUT_SOURCE_LIST,
            *args,
            **kwargs,
        )
        state = self.hass.states.get(self.entity_id)
        assert state
        features = state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

        self.chars_speaker: list[str] = []

        self._supports_play_pause = features & (
            MediaPlayerEntityFeature.PLAY | MediaPlayerEntityFeature.PAUSE
        )
        if (
            features & MediaPlayerEntityFeature.VOLUME_MUTE
            or features & MediaPlayerEntityFeature.VOLUME_STEP
        ):
            self.chars_speaker.extend(
                (CHAR_NAME, CHAR_ACTIVE, CHAR_VOLUME_CONTROL_TYPE, CHAR_VOLUME_SELECTOR)
            )
            if features & MediaPlayerEntityFeature.VOLUME_SET:
                self.chars_speaker.append(CHAR_VOLUME)

        if CHAR_VOLUME_SELECTOR in self.chars_speaker:
            serv_speaker = self.add_preload_service(
                SERV_TELEVISION_SPEAKER, self.chars_speaker
            )
            self.serv_tv.add_linked_service(serv_speaker)

            name = f"{self.display_name} Volume"
            serv_speaker.configure_char(CHAR_NAME, value=name)
            serv_speaker.configure_char(CHAR_ACTIVE, value=1)

            self.char_mute = serv_speaker.configure_char(
                CHAR_MUTE, value=False, setter_callback=self.set_mute
            )

            volume_control_type = 1 if CHAR_VOLUME in self.chars_speaker else 2
            serv_speaker.configure_char(
                CHAR_VOLUME_CONTROL_TYPE, value=volume_control_type
            )

            self.char_volume_selector = serv_speaker.configure_char(
                CHAR_VOLUME_SELECTOR, setter_callback=self.set_volume_step
            )

            if CHAR_VOLUME in self.chars_speaker:
                self.char_volume = serv_speaker.configure_char(
                    CHAR_VOLUME, setter_callback=self.set_volume
                )

        self.async_update_state(state)