async def _async_update_data(self) -> TwinklyData:
        """Fetch data from Twinkly."""
        movies: list[dict[str, Any]] = []
        current_movie: dict[str, Any] = {}
        try:
            device_info = await self.client.get_details()
            brightness = await self.client.get_brightness()
            is_on = await self.client.is_on()
            mode_data = await self.client.get_mode()
            current_mode = mode_data.get("mode")
            if self.supports_effects:
                movies = (await self.client.get_saved_movies())["movies"]
        except (TimeoutError, ClientError) as exception:
            raise UpdateFailed from exception
        if self.supports_effects:
            try:
                current_movie = await self.client.get_current_movie()
            except (TwinklyError, TimeoutError, ClientError) as exception:
                _LOGGER.debug("Error fetching current movie: %s", exception)
        brightness = (
            int(brightness["value"]) if brightness["mode"] == "enabled" else 100
        )
        brightness = int(round(brightness * 2.55)) if is_on else 0
        if self.device_name != device_info[DEV_NAME]:
            self._async_update_device_info(device_info[DEV_NAME])
        return TwinklyData(
            device_info,
            brightness,
            is_on,
            {movie["id"]: movie["name"] for movie in movies},
            current_movie.get("id"),
            current_mode,
        )