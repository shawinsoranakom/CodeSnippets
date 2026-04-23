async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        if not self._still_image_url:
            return None
        try:
            url = self._still_image_url.async_render(parse_result=False)
        except TemplateError as err:
            _LOGGER.error("Error parsing template %s: %s", self._still_image_url, err)
            return self._last_image

        try:
            vol.Schema(vol.Url())(url)
        except vol.Invalid as err:
            _LOGGER.warning("Invalid URL '%s': %s, returning last image", url, err)
            return self._last_image

        if url == self._last_url and self._limit_refetch:
            return self._last_image

        async with self._update_lock:
            if (
                self._last_image is not None
                and url == self._last_url
                and self._last_update + timedelta(0, self._attr_frame_interval)
                > datetime.now()
            ):
                return self._last_image

            try:
                update_time = datetime.now()
                async_client = get_async_client(self.hass, verify_ssl=self.verify_ssl)
                response = await async_client.get(
                    url,
                    auth=self._auth,
                    follow_redirects=True,
                    timeout=GET_IMAGE_TIMEOUT,
                )
                response.raise_for_status()
                self._last_image = response.content
                self._last_update = update_time

            except httpx.TimeoutException:
                _LOGGER.error("Timeout getting camera image from %s", self._name)
                return self._last_image
            except (httpx.RequestError, httpx.HTTPStatusError) as err:
                _LOGGER.error(
                    "Error getting new camera image from %s: %s", self._name, err
                )
                return self._last_image

            self._last_url = url
            return self._last_image