async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        now = time.monotonic()

        if self._image and now - self._last_update < self.IMAGE_INTERVAL:
            return self._image

        # Don't try to capture a new image if a stream is running
        if self._http_mpeg_stream_running:
            return self._image

        if self._can_stream and (video_url := self._video_url):
            # Sometimes the front end makes multiple image requests
            async with self._image_lock:
                if self._image and (now - self._last_update) < self.IMAGE_INTERVAL:
                    return self._image

                _LOGGER.debug("Updating camera image for %s", self._device.host)
                image = await ffmpeg.async_get_image(
                    self.hass,
                    video_url,
                    width=width,
                    height=height,
                )
                if image:
                    self._image = image
                    self._last_update = now
                    _LOGGER.debug("Updated camera image for %s", self._device.host)
                # This coroutine is called by camera with an asyncio.timeout
                # so image could be None whereas an auth issue returns b''
                elif image == b"":
                    _LOGGER.debug(
                        "Empty camera image returned for %s", self._device.host
                    )
                    # image could be empty if a stream is running so check for explicit auth error
                    await self._async_check_stream_auth(video_url)
                else:
                    _LOGGER.debug(
                        "None camera image returned for %s", self._device.host
                    )

        return self._image