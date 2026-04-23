async def async_turn_on(self, **kwargs):
        """Turn the specified or all lights on."""
        command = {"on": True}

        if ATTR_TRANSITION in kwargs:
            command["transitiontime"] = int(kwargs[ATTR_TRANSITION] * 10)

        if ATTR_HS_COLOR in kwargs:
            if self.is_osram:
                command["hue"] = int(kwargs[ATTR_HS_COLOR][0] / 360 * 65535)
                command["sat"] = int(kwargs[ATTR_HS_COLOR][1] / 100 * 255)
            else:
                # Philips hue bulb models respond differently to hue/sat
                # requests, so we convert to XY first to ensure a consistent
                # color.
                xy_color = color_util.color_hs_to_xy(*kwargs[ATTR_HS_COLOR], self.gamut)
                command["xy"] = xy_color
        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            temp_k = max(
                self.min_color_temp_kelvin,
                min(self.max_color_temp_kelvin, kwargs[ATTR_COLOR_TEMP_KELVIN]),
            )
            command["ct"] = color_util.color_temperature_kelvin_to_mired(temp_k)

        if ATTR_BRIGHTNESS in kwargs:
            command["bri"] = hass_to_hue_brightness(kwargs[ATTR_BRIGHTNESS])

        flash = kwargs.get(ATTR_FLASH)

        if flash == FLASH_LONG:
            command["alert"] = "lselect"
            del command["on"]
        elif flash == FLASH_SHORT:
            command["alert"] = "select"
            del command["on"]
        elif (
            not self.is_innr
            and not self.is_ewelink
            and not self.is_livarno
            and not self.is_s31litezb
        ):
            command["alert"] = "none"

        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            if effect == EFFECT_COLORLOOP:
                command["effect"] = "colorloop"
            elif effect == EFFECT_RANDOM:
                command["hue"] = random.randrange(0, 65535)
                command["sat"] = random.randrange(150, 254)
            else:
                command["effect"] = "none"

        if self.is_group:
            await self.bridge.async_request_call(self.light.set_action, **command)
        else:
            await self.bridge.async_request_call(self.light.set_state, **command)

        await self.coordinator.async_request_refresh()