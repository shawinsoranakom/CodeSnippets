async def set_state(self, **kwargs: Any) -> None:
        """Set a color on the light and turn it on/off."""
        self.coordinator.async_set_updated_data(None)
        # Cancel any pending refreshes
        bulb = self.bulb

        await self.effects_conductor.stop([bulb])

        if ATTR_EFFECT in kwargs:
            await self.default_effect(**kwargs)
            return

        if ATTR_INFRARED in kwargs:
            infrared_entity_id = self.coordinator.async_get_entity_id(
                Platform.SELECT, INFRARED_BRIGHTNESS
            )
            _LOGGER.warning(
                (
                    "The 'infrared' attribute of 'lifx.set_state' is deprecated:"
                    " call 'select.select_option' targeting '%s' instead"
                ),
                infrared_entity_id,
            )
            bulb.set_infrared(convert_8_to_16(kwargs[ATTR_INFRARED]))

        fade = int(kwargs.get(ATTR_TRANSITION, 0) * 1000)

        if ATTR_BRIGHTNESS_STEP in kwargs or ATTR_BRIGHTNESS_STEP_PCT in kwargs:
            brightness = self.brightness if self.is_on and self.brightness else 0

            if ATTR_BRIGHTNESS_STEP in kwargs:
                brightness += kwargs.pop(ATTR_BRIGHTNESS_STEP)

            else:
                brightness_pct = round(brightness / 255 * 100)
                brightness = round(
                    (brightness_pct + kwargs.pop(ATTR_BRIGHTNESS_STEP_PCT)) / 100 * 255
                )

            kwargs[ATTR_BRIGHTNESS] = max(0, min(255, brightness))

        # These are both False if ATTR_POWER is not set
        power_on = kwargs.get(ATTR_POWER, False)
        power_off = not kwargs.get(ATTR_POWER, True)

        hsbk = find_hsbk(self.hass, **kwargs)

        if not self.is_on:
            if power_off:
                await self.set_power(False)
            # If fading on with color, set color immediately
            if hsbk and power_on:
                await self.set_color(hsbk, kwargs)
                await self.set_power(True, duration=fade)
            elif hsbk:
                await self.set_color(hsbk, kwargs, duration=fade)
            elif power_on:
                await self.set_power(True, duration=fade)
        else:
            if power_on:
                await self.set_power(True)
            if hsbk:
                await self.set_color(hsbk, kwargs, duration=fade)
            if power_off:
                await self.set_power(False, duration=fade)

        # Avoid state ping-pong by holding off updates as the state settles
        await asyncio.sleep(LIFX_STATE_SETTLE_DELAY)

        # Update when the transition starts and ends
        await self.update_during_transition(fade)