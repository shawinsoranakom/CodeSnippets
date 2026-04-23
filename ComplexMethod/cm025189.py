async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn device on."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(int(kwargs[ATTR_BRIGHTNESS]) / 2.55)

            # If brightness is 0, the twinkly will only "disable" the brightness,
            # which means that it will be 100%.
            if brightness == 0:
                await self.client.turn_off()
                return

            await self.client.set_brightness(brightness)

        if (
            ATTR_RGBW_COLOR in kwargs
            and kwargs[ATTR_RGBW_COLOR] != self._attr_rgbw_color
        ):
            await self.client.interview()
            if LightEntityFeature.EFFECT & self.supported_features:
                await self.client.set_static_colour(
                    (
                        kwargs[ATTR_RGBW_COLOR][3],
                        kwargs[ATTR_RGBW_COLOR][0],
                        kwargs[ATTR_RGBW_COLOR][1],
                        kwargs[ATTR_RGBW_COLOR][2],
                    )
                )
                await self.client.set_mode("color")
                self.client.default_mode = "color"
            else:
                await self.client.set_cycle_colours(
                    (
                        kwargs[ATTR_RGBW_COLOR][3],
                        kwargs[ATTR_RGBW_COLOR][0],
                        kwargs[ATTR_RGBW_COLOR][1],
                        kwargs[ATTR_RGBW_COLOR][2],
                    )
                )
                await self.client.set_mode("movie")
                self.client.default_mode = "movie"
            self._attr_rgbw_color = kwargs[ATTR_RGBW_COLOR]

        if ATTR_RGB_COLOR in kwargs and kwargs[ATTR_RGB_COLOR] != self._attr_rgb_color:
            await self.client.interview()
            if LightEntityFeature.EFFECT & self.supported_features:
                await self.client.set_static_colour(kwargs[ATTR_RGB_COLOR])
                await self.client.set_mode("color")
                self.client.default_mode = "color"
            else:
                await self.client.set_cycle_colours(kwargs[ATTR_RGB_COLOR])
                await self.client.set_mode("movie")
                self.client.default_mode = "movie"

            self._attr_rgb_color = kwargs[ATTR_RGB_COLOR]

        if (
            ATTR_EFFECT in kwargs
            and LightEntityFeature.EFFECT & self.supported_features
        ):
            movie_id = kwargs[ATTR_EFFECT].split(" ")[0]
            if (
                self.coordinator.data.current_movie is None
                or int(movie_id) != self.coordinator.data.current_movie
            ):
                await self.client.interview()
                await self.client.set_current_movie(int(movie_id))
                await self.client.set_mode("movie")
                self.client.default_mode = "movie"
        if not self._attr_is_on:
            await self.client.turn_on()
        await self.coordinator.async_refresh()