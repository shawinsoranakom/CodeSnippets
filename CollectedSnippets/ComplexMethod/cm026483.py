def interfaces(self) -> Generator[AlexaCapability]:
        """Yield the supported interfaces."""
        yield AlexaPowerController(self.entity)

        supported = self.entity.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        if supported & media_player.MediaPlayerEntityFeature.VOLUME_SET:
            yield AlexaSpeaker(self.entity)
        elif supported & media_player.MediaPlayerEntityFeature.VOLUME_STEP:
            yield AlexaStepSpeaker(self.entity)

        playback_features = (
            media_player.MediaPlayerEntityFeature.PLAY
            | media_player.MediaPlayerEntityFeature.PAUSE
            | media_player.MediaPlayerEntityFeature.STOP
            | media_player.MediaPlayerEntityFeature.NEXT_TRACK
            | media_player.MediaPlayerEntityFeature.PREVIOUS_TRACK
        )
        if supported & playback_features:
            yield AlexaPlaybackController(self.entity)
            yield AlexaPlaybackStateReporter(self.entity)

        if supported & media_player.MediaPlayerEntityFeature.SEEK:
            yield AlexaSeekController(self.entity)

        if supported & media_player.MediaPlayerEntityFeature.SELECT_SOURCE:
            inputs = AlexaInputController.get_valid_inputs(
                self.entity.attributes.get(media_player.ATTR_INPUT_SOURCE_LIST, [])
            )
            if len(inputs) > 0:
                yield AlexaInputController(self.entity)

        if supported & media_player.MediaPlayerEntityFeature.PLAY_MEDIA:
            yield AlexaChannelController(self.entity)

        # AlexaEqualizerController is disabled for denonavr
        # since it blocks alexa from discovering any devices.
        entity_info = entity_sources(self.hass).get(self.entity_id)
        domain = entity_info["domain"] if entity_info else None
        if (
            supported & media_player.MediaPlayerEntityFeature.SELECT_SOUND_MODE
            and domain != "denonavr"
        ):
            inputs = AlexaEqualizerController.get_valid_inputs(
                self.entity.attributes.get(media_player.ATTR_SOUND_MODE_LIST) or []
            )
            if len(inputs) > 0:
                yield AlexaEqualizerController(self.entity)

        yield AlexaEndpointHealth(self.hass, self.entity)
        yield Alexa(self.entity)