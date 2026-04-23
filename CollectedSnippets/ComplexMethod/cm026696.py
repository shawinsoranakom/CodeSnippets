async def async_play_media(
        self,
        media_type: MediaType | str,
        media_id: str,
        announce: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Play from: netradio station id, URI, favourite or Deezer."""
        # Convert audio/mpeg, audio/aac etc. to MediaType.MUSIC
        if media_type.startswith("audio/"):
            media_type = MediaType.MUSIC

        if media_type not in VALID_MEDIA_TYPES:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_media_type",
                translation_placeholders={
                    "invalid_media_type": media_type,
                    "valid_media_types": ",".join(VALID_MEDIA_TYPES),
                },
            )

        if media_source.is_media_source_id(media_id):
            sourced_media = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )

            media_id = async_process_play_media_url(self.hass, sourced_media.url)

            # Exit if the source uses unsupported file.
            if media_id.endswith(".m3u"):
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="m3u_invalid_format"
                )

        if announce:
            extra = kwargs.get(ATTR_MEDIA_EXTRA, {})

            absolute_volume = extra.get("overlay_absolute_volume", None)
            offset_volume = extra.get("overlay_offset_volume", None)
            tts_language = extra.get("overlay_tts_language", "en-us")

            # Construct request
            overlay_play_request = OverlayPlayRequest()

            # Define volume level
            if absolute_volume:
                overlay_play_request.volume_absolute = absolute_volume

            elif offset_volume:
                # Ensure that the volume is not above 100
                if not self._volume.level or not self._volume.level.level:
                    _LOGGER.warning("Error setting volume")
                else:
                    overlay_play_request.volume_absolute = min(
                        self._volume.level.level + offset_volume, 100
                    )

            if media_type == BeoMediaType.OVERLAY_TTS:
                # Bang & Olufsen cloud TTS
                overlay_play_request.text_to_speech = (
                    OverlayPlayRequestTextToSpeechTextToSpeech(
                        lang=tts_language, text=media_id
                    )
                )
            else:
                overlay_play_request.uri = Uri(location=media_id)

            await self._client.post_overlay_play(overlay_play_request)

        elif media_type in (MediaType.URL, MediaType.MUSIC):
            await self._client.post_uri_source(uri=Uri(location=media_id))

        # The "provider" media_type may not be suitable for overlay all the time.
        # Use it for now.
        elif media_type == BeoMediaType.TTS:
            await self._client.post_overlay_play(
                overlay_play_request=OverlayPlayRequest(
                    uri=Uri(location=media_id),
                )
            )

        elif media_type == BeoMediaType.RADIO:
            await self._client.run_provided_scene(
                scene_properties=SceneProperties(
                    action_list=[
                        Action(
                            type="radio",
                            radio_station_id=media_id,
                        )
                    ]
                )
            )

        elif media_type == BeoMediaType.FAVOURITE:
            await self._client.activate_preset(id=int(media_id))

        elif media_type in (BeoMediaType.DEEZER, BeoMediaType.TIDAL):
            try:
                # Play Deezer flow.
                if media_id == "flow" and media_type == BeoMediaType.DEEZER:
                    deezer_id = None

                    if "id" in kwargs[ATTR_MEDIA_EXTRA]:
                        deezer_id = kwargs[ATTR_MEDIA_EXTRA]["id"]

                    await self._client.start_deezer_flow(
                        user_flow=UserFlow(user_id=deezer_id)
                    )

                # Play a playlist or album.
                elif any(match in media_id for match in ("playlist", "album")):
                    start_from = 0
                    if "start_from" in kwargs[ATTR_MEDIA_EXTRA]:
                        start_from = kwargs[ATTR_MEDIA_EXTRA]["start_from"]

                    await self._client.add_to_queue(
                        play_queue_item=PlayQueueItem(
                            provider=PlayQueueItemType(value=media_type),
                            start_now_from_position=start_from,
                            type="playlist",
                            uri=media_id,
                        )
                    )

                # Play a track.
                else:
                    await self._client.add_to_queue(
                        play_queue_item=PlayQueueItem(
                            provider=PlayQueueItemType(value=media_type),
                            start_now_from_position=0,
                            type="track",
                            uri=media_id,
                        )
                    )

            except ApiException as error:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="play_media_error",
                    translation_placeholders={
                        "media_type": media_type,
                        "error_message": json.loads(cast(str, error.body))["message"],
                    },
                ) from error