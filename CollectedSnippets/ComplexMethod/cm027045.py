async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play media from a URL or file, launch an application, or tune to a channel."""
        extra: dict[str, Any] = kwargs.get(ATTR_MEDIA_EXTRA) or {}
        original_media_type: str = media_type
        original_media_id: str = media_id
        mime_type: str | None = None
        stream_name: str | None = None
        stream_format: str | None = extra.get(ATTR_FORMAT)

        # Handle media_source
        if media_source.is_media_source_id(media_id):
            sourced_media = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )
            media_type = MediaType.URL
            media_id = sourced_media.url
            mime_type = sourced_media.mime_type
            stream_name = original_media_id
            stream_format = guess_stream_format(media_id, mime_type)

        if media_type == FORMAT_CONTENT_TYPE[HLS_PROVIDER]:
            media_type = MediaType.VIDEO
            mime_type = FORMAT_CONTENT_TYPE[HLS_PROVIDER]
            stream_name = "Camera Stream"
            stream_format = "hls"

        if media_type in {MediaType.MUSIC, MediaType.URL, MediaType.VIDEO}:
            # If media ID is a relative URL, we serve it from HA.
            media_id = async_process_play_media_url(self.hass, media_id)

            parsed = yarl.URL(media_id)

            if mime_type is None:
                mime_type, _ = mimetypes.guess_type(parsed.path)

            if stream_format is None:
                stream_format = guess_stream_format(media_id, mime_type)

            if extra.get(ATTR_FORMAT) is None:
                extra[ATTR_FORMAT] = stream_format

            if extra[ATTR_FORMAT] not in STREAM_FORMAT_TO_MEDIA_TYPE:
                _LOGGER.error(
                    "Media type %s is not supported with format %s (mime: %s)",
                    original_media_type,
                    extra[ATTR_FORMAT],
                    mime_type,
                )
                return

            if (
                media_type == MediaType.URL
                and STREAM_FORMAT_TO_MEDIA_TYPE[extra[ATTR_FORMAT]] == MediaType.MUSIC
            ):
                media_type = MediaType.MUSIC

            if media_type == MediaType.MUSIC and "tts_proxy" in media_id:
                stream_name = "Text to Speech"
            elif stream_name is None:
                if stream_format == "ism":
                    stream_name = parsed.parts[-2]
                else:
                    stream_name = parsed.name

            if extra.get(ATTR_NAME) is None:
                extra[ATTR_NAME] = stream_name

        if media_type == MediaType.APP:
            params = {
                param: extra[attr]
                for attr, param in ATTRS_TO_LAUNCH_PARAMS.items()
                if attr in extra
            }

            await self.coordinator.roku.launch(media_id, params)
        elif media_type == MediaType.CHANNEL:
            await self.coordinator.roku.tune(media_id)
        elif media_type == MediaType.MUSIC:
            if extra.get(ATTR_ARTIST_NAME) is None:
                extra[ATTR_ARTIST_NAME] = "Home Assistant"

            params = {
                param: extra[attr]
                for (attr, param) in ATTRS_TO_PLAY_ON_ROKU_AUDIO_PARAMS.items()
                if attr in extra
            }

            params = {"u": media_id, "t": "a", **params}

            await self.coordinator.roku.launch(
                self.coordinator.play_media_app_id,
                params,
            )
        elif media_type in {MediaType.URL, MediaType.VIDEO}:
            params = {
                param: extra[attr]
                for (attr, param) in ATTRS_TO_PLAY_ON_ROKU_PARAMS.items()
                if attr in extra
            }
            params["u"] = media_id
            params["t"] = "v"

            await self.coordinator.roku.launch(
                self.coordinator.play_media_app_id,
                params,
            )
        else:
            _LOGGER.error("Media type %s is not supported", original_media_type)
            return

        await self.coordinator.async_request_refresh()