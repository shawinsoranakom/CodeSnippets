async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        data: dict[str, Any] = {
            ATTR_ON: True,
            ATTR_SEGMENT_ID: self._segment,
        }

        if ATTR_RGB_COLOR in kwargs:
            data[ATTR_COLOR_PRIMARY] = kwargs[ATTR_RGB_COLOR]

        if ATTR_RGBW_COLOR in kwargs:
            data[ATTR_COLOR_PRIMARY] = kwargs[ATTR_RGBW_COLOR]

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            data[ATTR_CCT] = kelvin_to_255(
                kwargs[ATTR_COLOR_TEMP_KELVIN], COLOR_TEMP_K_MIN, COLOR_TEMP_K_MAX
            )

        if ATTR_TRANSITION in kwargs:
            # WLED uses 100ms per unit, so 10 = 1 second.
            data[ATTR_TRANSITION] = round(kwargs[ATTR_TRANSITION] * 10)

        if ATTR_BRIGHTNESS in kwargs:
            data[ATTR_BRIGHTNESS] = kwargs[ATTR_BRIGHTNESS]

        if ATTR_EFFECT in kwargs:
            data[ATTR_EFFECT] = kwargs[ATTR_EFFECT]

        # If there is no main control, and only 1 segment, handle the main
        if not self.coordinator.has_main_light:
            main_data = {ATTR_ON: True}
            if ATTR_BRIGHTNESS in data:
                main_data[ATTR_BRIGHTNESS] = data[ATTR_BRIGHTNESS]
                data[ATTR_BRIGHTNESS] = 255

            if ATTR_TRANSITION in data:
                main_data[ATTR_TRANSITION] = data[ATTR_TRANSITION]
                del data[ATTR_TRANSITION]

            await self.coordinator.wled.segment(**data)
            await self.coordinator.wled.master(**main_data)
            return

        await self.coordinator.wled.segment(**data)