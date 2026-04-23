async def _do_announce(
        self,
        announcement: assist_satellite.AssistSatelliteAnnouncement,
        run_pipeline_after: bool,
    ) -> None:
        """Announce media on the satellite.

        Optionally run a voice pipeline after the announcement has finished.
        """
        _LOGGER.debug(
            "Waiting for announcement to finished (message=%s, media_id=%s)",
            announcement.message,
            announcement.media_id,
        )
        media_id = announcement.media_id
        is_media_tts = announcement.media_id_source == "tts"
        preannounce_media_id = announcement.preannounce_media_id
        if (not is_media_tts) or preannounce_media_id:
            # Route media through the proxy
            format_to_use: MediaPlayerSupportedFormat | None = None
            for supported_format in chain(
                *self._entry_data.media_player_formats.values()
            ):
                if supported_format.purpose == MediaPlayerFormatPurpose.ANNOUNCEMENT:
                    format_to_use = supported_format
                    break

            if format_to_use is not None:
                assert (self.registry_entry is not None) and (
                    self.registry_entry.device_id is not None
                )

                make_proxy_url = partial(
                    async_create_proxy_url,
                    hass=self.hass,
                    device_id=self.registry_entry.device_id,
                    media_format=format_to_use.format,
                    rate=format_to_use.sample_rate or None,
                    channels=format_to_use.num_channels or None,
                    width=format_to_use.sample_bytes or None,
                )

                if not is_media_tts:
                    media_id = async_process_play_media_url(
                        self.hass, make_proxy_url(media_url=media_id)
                    )

                if preannounce_media_id:
                    preannounce_media_id = async_process_play_media_url(
                        self.hass, make_proxy_url(media_url=preannounce_media_id)
                    )

        await self.cli.send_voice_assistant_announcement_await_response(
            media_id,
            _ANNOUNCEMENT_TIMEOUT_SEC,
            announcement.message,
            start_conversation=run_pipeline_after,
            preannounce_media_id=preannounce_media_id or "",
        )