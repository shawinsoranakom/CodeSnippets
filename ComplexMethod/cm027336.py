async def async_turn_on(self, **kwargs: Any) -> None:  # noqa: C901
        """Turn the device on.

        This method is a coroutine.
        """
        should_update = False
        on_command_type: str = self._config[CONF_ON_COMMAND_TYPE]

        async def publish(topic: str, payload: PublishPayloadType) -> None:
            """Publish an MQTT message."""
            await self.async_publish_with_config(str(self._topic[topic]), payload)

        def scale_rgbx(
            color: tuple[int, ...],
            brightness: int | None = None,
        ) -> tuple[int, ...]:
            """Scale RGBx for brightness."""
            if brightness is None:
                # If there's a brightness topic set, we don't want to scale the RGBx
                # values given using the brightness.
                if self._topic[CONF_BRIGHTNESS_COMMAND_TOPIC] is not None:
                    brightness = 255
                else:
                    brightness = kwargs.get(ATTR_BRIGHTNESS) or self.brightness or 255
            return tuple(int(channel * brightness / 255) for channel in color)

        def render_rgbx(
            color: tuple[int, ...],
            template: str,
            color_mode: ColorMode,
        ) -> PublishPayloadType:
            """Render RGBx payload."""
            rgb_color_str = ",".join(str(channel) for channel in color)
            keys = ["red", "green", "blue"]
            if color_mode == ColorMode.RGBW:
                keys.append("white")
            elif color_mode == ColorMode.RGBWW:
                keys.extend(["cold_white", "warm_white"])
            variables = dict(zip(keys, color, strict=False))
            return self._command_templates[template](rgb_color_str, variables)

        def set_optimistic(
            attribute: str,
            value: Any,
            color_mode: ColorMode | None = None,
            condition_attribute: str | None = None,
        ) -> bool:
            """Optimistically update a state attribute."""
            if condition_attribute is None:
                condition_attribute = attribute
            if not self._is_optimistic(condition_attribute):
                return False
            if color_mode and self._optimistic_color_mode:
                self._attr_color_mode = color_mode

            setattr(self, f"_attr_{attribute}", value)
            return True

        if on_command_type == "first":
            await publish(CONF_COMMAND_TOPIC, self._payload["on"])
            should_update = True

        # If brightness is being used instead of an on command, make sure
        # there is a brightness input.  Either set the brightness to our
        # saved value or the maximum value if this is the first call
        elif (
            on_command_type == "brightness"
            and ATTR_BRIGHTNESS not in kwargs
            and ATTR_WHITE not in kwargs
        ):
            kwargs[ATTR_BRIGHTNESS] = self.brightness or 255

        hs_color: str | None = kwargs.get(ATTR_HS_COLOR)

        if hs_color and self._topic[CONF_HS_COMMAND_TOPIC] is not None:
            device_hs_payload = self._command_templates[CONF_HS_COMMAND_TEMPLATE](
                f"{hs_color[0]},{hs_color[1]}",
                {"hue": hs_color[0], "sat": hs_color[1]},
            )
            await publish(CONF_HS_COMMAND_TOPIC, device_hs_payload)
            should_update |= set_optimistic(ATTR_HS_COLOR, hs_color, ColorMode.HS)

        rgb: tuple[int, int, int] | None
        if (rgb := kwargs.get(ATTR_RGB_COLOR)) and self._topic[
            CONF_RGB_COMMAND_TOPIC
        ] is not None:
            scaled = scale_rgbx(rgb)
            rgb_s = render_rgbx(scaled, CONF_RGB_COMMAND_TEMPLATE, ColorMode.RGB)
            await publish(CONF_RGB_COMMAND_TOPIC, rgb_s)
            should_update |= set_optimistic(ATTR_RGB_COLOR, rgb, ColorMode.RGB)

        rgbw: tuple[int, int, int, int] | None
        if (rgbw := kwargs.get(ATTR_RGBW_COLOR)) and self._topic[
            CONF_RGBW_COMMAND_TOPIC
        ] is not None:
            scaled = scale_rgbx(rgbw)
            rgbw_s = render_rgbx(scaled, CONF_RGBW_COMMAND_TEMPLATE, ColorMode.RGBW)
            await publish(CONF_RGBW_COMMAND_TOPIC, rgbw_s)
            should_update |= set_optimistic(ATTR_RGBW_COLOR, rgbw, ColorMode.RGBW)

        rgbww: tuple[int, int, int, int, int] | None
        if (rgbww := kwargs.get(ATTR_RGBWW_COLOR)) and self._topic[
            CONF_RGBWW_COMMAND_TOPIC
        ] is not None:
            scaled = scale_rgbx(rgbww)
            rgbww_s = render_rgbx(scaled, CONF_RGBWW_COMMAND_TEMPLATE, ColorMode.RGBWW)
            await publish(CONF_RGBWW_COMMAND_TOPIC, rgbww_s)
            should_update |= set_optimistic(ATTR_RGBWW_COLOR, rgbww, ColorMode.RGBWW)

        xy_color: tuple[float, float] | None
        if (xy_color := kwargs.get(ATTR_XY_COLOR)) and self._topic[
            CONF_XY_COMMAND_TOPIC
        ] is not None:
            device_xy_payload = self._command_templates[CONF_XY_COMMAND_TEMPLATE](
                f"{xy_color[0]},{xy_color[1]}",
                {"x": xy_color[0], "y": xy_color[1]},
            )
            await publish(CONF_XY_COMMAND_TOPIC, device_xy_payload)
            should_update |= set_optimistic(ATTR_XY_COLOR, xy_color, ColorMode.XY)

        if (
            ATTR_BRIGHTNESS in kwargs
            and self._topic[CONF_BRIGHTNESS_COMMAND_TOPIC] is not None
        ):
            brightness_normalized: float = kwargs[ATTR_BRIGHTNESS] / 255
            brightness_scale: int = self._config[CONF_BRIGHTNESS_SCALE]
            device_brightness = min(
                round(brightness_normalized * brightness_scale), brightness_scale
            )
            # Make sure the brightness is not rounded down to 0
            device_brightness = max(device_brightness, 1)
            command_tpl = self._command_templates[CONF_BRIGHTNESS_COMMAND_TEMPLATE]
            device_brightness_payload = command_tpl(device_brightness, None)
            await publish(CONF_BRIGHTNESS_COMMAND_TOPIC, device_brightness_payload)
            should_update |= set_optimistic(ATTR_BRIGHTNESS, kwargs[ATTR_BRIGHTNESS])
        elif (
            ATTR_BRIGHTNESS in kwargs
            and ATTR_RGB_COLOR not in kwargs
            and self._topic[CONF_RGB_COMMAND_TOPIC] is not None
        ):
            rgb_color = self.rgb_color or (255,) * 3
            rgb_scaled = scale_rgbx(rgb_color, kwargs[ATTR_BRIGHTNESS])
            rgb_s = render_rgbx(rgb_scaled, CONF_RGB_COMMAND_TEMPLATE, ColorMode.RGB)
            await publish(CONF_RGB_COMMAND_TOPIC, rgb_s)
            should_update |= set_optimistic(ATTR_BRIGHTNESS, kwargs[ATTR_BRIGHTNESS])
        elif (
            ATTR_BRIGHTNESS in kwargs
            and ATTR_RGBW_COLOR not in kwargs
            and self._topic[CONF_RGBW_COMMAND_TOPIC] is not None
        ):
            rgbw_color = self.rgbw_color or (255,) * 4
            rgbw_b = scale_rgbx(rgbw_color, kwargs[ATTR_BRIGHTNESS])
            rgbw_s = render_rgbx(rgbw_b, CONF_RGBW_COMMAND_TEMPLATE, ColorMode.RGBW)
            await publish(CONF_RGBW_COMMAND_TOPIC, rgbw_s)
            should_update |= set_optimistic(ATTR_BRIGHTNESS, kwargs[ATTR_BRIGHTNESS])
        elif (
            ATTR_BRIGHTNESS in kwargs
            and ATTR_RGBWW_COLOR not in kwargs
            and self._topic[CONF_RGBWW_COMMAND_TOPIC] is not None
        ):
            rgbww_color = self.rgbww_color or (255,) * 5
            rgbww_b = scale_rgbx(rgbww_color, kwargs[ATTR_BRIGHTNESS])
            rgbww_s = render_rgbx(rgbww_b, CONF_RGBWW_COMMAND_TEMPLATE, ColorMode.RGBWW)
            await publish(CONF_RGBWW_COMMAND_TOPIC, rgbww_s)
            should_update |= set_optimistic(ATTR_BRIGHTNESS, kwargs[ATTR_BRIGHTNESS])
        if (
            ATTR_COLOR_TEMP_KELVIN in kwargs
            and self._topic[CONF_COLOR_TEMP_COMMAND_TOPIC] is not None
        ):
            ct_command_tpl = self._command_templates[CONF_COLOR_TEMP_COMMAND_TEMPLATE]
            color_temp = ct_command_tpl(
                kwargs[ATTR_COLOR_TEMP_KELVIN]
                if self._color_temp_kelvin
                else color_util.color_temperature_kelvin_to_mired(
                    kwargs[ATTR_COLOR_TEMP_KELVIN]
                ),
                None,
            )
            await publish(CONF_COLOR_TEMP_COMMAND_TOPIC, color_temp)
            should_update |= set_optimistic(
                ATTR_COLOR_TEMP_KELVIN,
                kwargs[ATTR_COLOR_TEMP_KELVIN],
                ColorMode.COLOR_TEMP,
            )

        if (
            ATTR_EFFECT in kwargs
            and self._topic[CONF_EFFECT_COMMAND_TOPIC] is not None
            and CONF_EFFECT_LIST in self._config
        ):
            if kwargs[ATTR_EFFECT] in self._config[CONF_EFFECT_LIST]:
                eff_command_tpl = self._command_templates[CONF_EFFECT_COMMAND_TEMPLATE]
                effect = eff_command_tpl(kwargs[ATTR_EFFECT], None)
                await publish(CONF_EFFECT_COMMAND_TOPIC, effect)
                should_update |= set_optimistic(ATTR_EFFECT, kwargs[ATTR_EFFECT])

        if ATTR_WHITE in kwargs and self._topic[CONF_WHITE_COMMAND_TOPIC] is not None:
            percent_white = float(kwargs[ATTR_WHITE]) / 255
            white_scale: int = self._config[CONF_WHITE_SCALE]
            device_white_value = min(round(percent_white * white_scale), white_scale)
            await publish(CONF_WHITE_COMMAND_TOPIC, device_white_value)
            should_update |= set_optimistic(
                ATTR_BRIGHTNESS,
                kwargs[ATTR_WHITE],
                ColorMode.WHITE,
            )

        if on_command_type == "last":
            await publish(CONF_COMMAND_TOPIC, self._payload["on"])
            should_update = True

        if self._optimistic:
            # Optimistically assume that the light has changed state.
            self._attr_is_on = True
            should_update = True

        if should_update:
            self.async_write_ha_state()