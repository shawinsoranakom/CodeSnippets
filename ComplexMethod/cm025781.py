async def _resolve_announcement_media_id(
        self,
        message: str,
        media_id: str | None,
        preannounce_media_id: str | None = None,
    ) -> AssistSatelliteAnnouncement:
        """Resolve the media ID."""
        media_id_source: Literal["url", "media_id", "tts"] | None = None
        tts_token: str | None = None

        if media_id:
            original_media_id = media_id
        else:
            media_id_source = "tts"
            # Synthesize audio and get URL
            pipeline_id = self._resolve_pipeline()
            pipeline = async_get_pipeline(self.hass, pipeline_id)

            engine = tts.async_resolve_engine(self.hass, pipeline.tts_engine)
            if engine is None:
                raise HomeAssistantError(f"TTS engine {pipeline.tts_engine} not found")

            tts_options: dict[str, Any] = {}
            if pipeline.tts_voice is not None:
                tts_options[tts.ATTR_VOICE] = pipeline.tts_voice

            if self.tts_options is not None:
                tts_options.update(self.tts_options)

            stream = tts.async_create_stream(
                self.hass,
                engine=engine,
                language=pipeline.tts_language,
                options=tts_options,
            )
            stream.async_set_message(message)

            tts_token = stream.token
            media_id = stream.url
            original_media_id = tts.generate_media_source_id(
                self.hass,
                message,
                engine=engine,
                language=pipeline.tts_language,
                options=tts_options,
            )

        if media_source.is_media_source_id(media_id):
            if not media_id_source:
                media_id_source = "media_id"
            media = await media_source.async_resolve_media(
                self.hass,
                media_id,
                None,
            )
            media_id = media.url

        if not media_id_source:
            media_id_source = "url"

        # Resolve to full URL
        media_id = async_process_play_media_url(self.hass, media_id)

        # Resolve preannounce media id
        if preannounce_media_id:
            if media_source.is_media_source_id(preannounce_media_id):
                preannounce_media = await media_source.async_resolve_media(
                    self.hass,
                    preannounce_media_id,
                    None,
                )
                preannounce_media_id = preannounce_media.url

            # Resolve to full URL
            preannounce_media_id = async_process_play_media_url(
                self.hass, preannounce_media_id
            )

        return AssistSatelliteAnnouncement(
            message=message,
            media_id=media_id,
            original_media_id=original_media_id,
            tts_token=tts_token,
            media_id_source=media_id_source,
            preannounce_media_id=preannounce_media_id,
        )