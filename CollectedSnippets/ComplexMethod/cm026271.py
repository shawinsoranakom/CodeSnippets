def _get_proxy_url(
        self,
        supported_formats: list[MediaPlayerSupportedFormat],
        url: str,
        announcement: bool,
    ) -> str | None:
        """Get URL for ffmpeg proxy."""
        # Choose the first default or announcement supported format
        format_to_use: MediaPlayerSupportedFormat | None = None
        for supported_format in supported_formats:
            if (format_to_use is None) and (
                supported_format.purpose == MediaPlayerFormatPurpose.DEFAULT
            ):
                # First default format
                format_to_use = supported_format
            elif announcement and (
                supported_format.purpose == MediaPlayerFormatPurpose.ANNOUNCEMENT
            ):
                # First announcement format
                format_to_use = supported_format
                break

        if format_to_use is None:
            # No format for conversion
            return None

        # Replace the media URL with a proxy URL pointing to Home
        # Assistant. When requested, Home Assistant will use ffmpeg to
        # convert the source URL to the supported format.
        _LOGGER.debug("Proxying media url %s with format %s", url, format_to_use)
        device_id = self.device_entry.id
        media_format = format_to_use.format

        # 0 = None
        rate: int | None = None
        channels: int | None = None
        width: int | None = None
        if format_to_use.sample_rate > 0:
            rate = format_to_use.sample_rate

        if format_to_use.num_channels > 0:
            channels = format_to_use.num_channels

        if format_to_use.sample_bytes > 0:
            width = format_to_use.sample_bytes

        proxy_url = async_create_proxy_url(
            self.hass,
            device_id,
            url,
            media_format=media_format,
            rate=rate,
            channels=channels,
            width=width,
        )

        # Resolve URL
        return async_process_play_media_url(self.hass, proxy_url)