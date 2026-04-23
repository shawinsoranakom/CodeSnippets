def _update_values(self) -> None:
        """Set base values from underlying lights of a group."""
        supported_color_modes: set[ColorMode] = set()
        lights_with_color_support = 0
        lights_with_color_temp_support = 0
        lights_with_dimming_support = 0
        lights_on_with_dimming_support = 0
        total_brightness = 0
        all_lights = self.controller.get_lights(self.resource.id)
        lights_in_colortemp_mode = 0
        lights_in_xy_mode = 0
        lights_in_dynamic_mode = 0
        # accumulate color values
        xy_total_x = 0.0
        xy_total_y = 0.0
        xy_count = 0
        temp_total = 0.0

        # loop through all lights to find capabilities
        for light in all_lights:
            # reset per-light colortemp on flag
            light_in_colortemp_mode = False
            # check if light has color temperature
            if color_temp := light.color_temperature:
                lights_with_color_temp_support += 1
                # default to mired values from the last capable light
                self._attr_color_temp_kelvin = (
                    color_util.color_temperature_mired_to_kelvin(color_temp.mirek)
                    if color_temp.mirek
                    else None
                )
                self._attr_min_color_temp_kelvin = (
                    color_util.color_temperature_mired_to_kelvin(
                        color_temp.mirek_schema.mirek_maximum
                    )
                )
                self._attr_max_color_temp_kelvin = (
                    color_util.color_temperature_mired_to_kelvin(
                        color_temp.mirek_schema.mirek_minimum
                    )
                )
                # counters for color mode vote and average temp
                if (
                    light.on.on
                    and color_temp.mirek is not None
                    and color_temp.mirek_valid
                ):
                    lights_in_colortemp_mode += 1
                    light_in_colortemp_mode = True
                    temp_total += color_util.color_temperature_mired_to_kelvin(
                        color_temp.mirek
                    )
            # check if light has color xy
            if color := light.color:
                lights_with_color_support += 1
                # default to xy values from the last capable light
                self._attr_xy_color = (color.xy.x, color.xy.y)
                # counters for color mode vote and average xy color
                if light.on.on:
                    xy_total_x += color.xy.x
                    xy_total_y += color.xy.y
                    xy_count += 1
                    # only count for colour mode vote if
                    # this light is not in colortemp mode
                    if not light_in_colortemp_mode:
                        lights_in_xy_mode += 1
            # check if light has dimming
            if dimming := light.dimming:
                lights_with_dimming_support += 1
                # accumulate brightness values
                if light.on.on:
                    total_brightness += dimming.brightness
                    lights_on_with_dimming_support += 1
            # check if light is in dynamic mode
            if (
                light.dynamics
                and light.dynamics.status == DynamicStatus.DYNAMIC_PALETTE
            ):
                lights_in_dynamic_mode += 1

        # this is a bit hacky because light groups may contain lights
        # of different capabilities
        # this means that the state is derived from only some of the lights
        # and will never be 100% accurate but it will be close

        # assign group color support modes based on light capabilities
        if lights_with_color_support > 0:
            supported_color_modes.add(ColorMode.XY)
        if lights_with_color_temp_support > 0:
            supported_color_modes.add(ColorMode.COLOR_TEMP)
        if lights_with_dimming_support > 0:
            if len(supported_color_modes) == 0:
                # only add color mode brightness if no color variants
                supported_color_modes.add(ColorMode.BRIGHTNESS)
            # as we have brightness support, set group brightness values
            if lights_on_with_dimming_support > 0:
                self._brightness_pct = total_brightness / lights_on_with_dimming_support
                self._attr_brightness = round(
                    ((total_brightness / lights_on_with_dimming_support) / 100) * 255
                )
        else:
            supported_color_modes.add(ColorMode.ONOFF)
        self._dynamic_mode_active = lights_in_dynamic_mode > 0
        self._attr_supported_color_modes = supported_color_modes
        # set the group color values if there are any color lights on
        if xy_count > 0:
            self._attr_xy_color = (
                round(xy_total_x / xy_count, 5),
                round(xy_total_y / xy_count, 5),
            )
        if lights_in_colortemp_mode > 0:
            avg_temp = temp_total / lights_in_colortemp_mode
            self._attr_color_temp_kelvin = round(avg_temp)
        # pick a winner for the current color mode based on the majority of on lights
        # if there is no winner pick the highest mode from group capabilities
        if lights_in_xy_mode > 0 and lights_in_xy_mode >= lights_in_colortemp_mode:
            self._attr_color_mode = ColorMode.XY
        elif (
            lights_in_colortemp_mode > 0
            and lights_in_colortemp_mode > lights_in_xy_mode
        ):
            self._attr_color_mode = ColorMode.COLOR_TEMP
        elif lights_with_color_support > 0:
            self._attr_color_mode = ColorMode.XY
        elif lights_with_color_temp_support > 0:
            self._attr_color_mode = ColorMode.COLOR_TEMP
        elif lights_with_dimming_support > 0:
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_color_mode = ColorMode.ONOFF