def async_update_group_state(self) -> None:
        """Query all members and determine the light group state."""
        self._update_assumed_state_from_members()

        states = [
            state
            for entity_id in self._entity_ids
            if (state := self.hass.states.get(entity_id)) is not None
        ]
        on_states = [state for state in states if state.state == STATE_ON]

        valid_state = self.mode(
            state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) for state in states
        )

        if not valid_state:
            # Set as unknown if any / all member is unknown or unavailable
            self._attr_is_on = None
        else:
            # Set as ON if any / all member is ON
            self._attr_is_on = self.mode(state.state == STATE_ON for state in states)

        self._attr_available = any(state.state != STATE_UNAVAILABLE for state in states)
        self._attr_brightness = reduce_attribute(on_states, ATTR_BRIGHTNESS)

        self._attr_hs_color = reduce_attribute(
            on_states, ATTR_HS_COLOR, reduce=mean_circle
        )
        self._attr_rgb_color = reduce_attribute(
            on_states, ATTR_RGB_COLOR, reduce=mean_tuple
        )
        self._attr_rgbw_color = reduce_attribute(
            on_states, ATTR_RGBW_COLOR, reduce=mean_tuple
        )
        self._attr_rgbww_color = reduce_attribute(
            on_states, ATTR_RGBWW_COLOR, reduce=mean_tuple
        )
        self._attr_xy_color = reduce_attribute(
            on_states, ATTR_XY_COLOR, reduce=mean_tuple
        )

        self._attr_color_temp_kelvin = reduce_attribute(
            on_states, ATTR_COLOR_TEMP_KELVIN
        )
        self._attr_min_color_temp_kelvin = reduce_attribute(
            states, ATTR_MIN_COLOR_TEMP_KELVIN, default=2000, reduce=min
        )
        self._attr_max_color_temp_kelvin = reduce_attribute(
            states, ATTR_MAX_COLOR_TEMP_KELVIN, default=6500, reduce=max
        )

        self._attr_effect_list = None
        all_effect_lists = list(find_state_attributes(states, ATTR_EFFECT_LIST))
        if all_effect_lists:
            # Merge all effects from all effect_lists with a union merge.
            self._attr_effect_list = list(set().union(*all_effect_lists))
            self._attr_effect_list.sort()
            if "None" in self._attr_effect_list:
                self._attr_effect_list.remove("None")
                self._attr_effect_list.insert(0, "None")

        self._attr_effect = None
        all_effects = list(find_state_attributes(on_states, ATTR_EFFECT))
        if all_effects:
            # Report the most common effect.
            effects_count = Counter(itertools.chain(all_effects))
            self._attr_effect = effects_count.most_common(1)[0][0]

        supported_color_modes = {ColorMode.ONOFF}
        all_supported_color_modes = list(
            find_state_attributes(states, ATTR_SUPPORTED_COLOR_MODES)
        )
        if all_supported_color_modes:
            # Merge all color modes.
            supported_color_modes = filter_supported_color_modes(
                cast(set[ColorMode], set().union(*all_supported_color_modes))
            )
        self._attr_supported_color_modes = supported_color_modes

        self._attr_color_mode = ColorMode.UNKNOWN
        all_color_modes = list(find_state_attributes(on_states, ATTR_COLOR_MODE))
        if all_color_modes:
            # Report the most common color mode, select brightness and onoff last
            color_mode_count = Counter(itertools.chain(all_color_modes))
            if ColorMode.ONOFF in color_mode_count:
                if ColorMode.ONOFF in supported_color_modes:
                    color_mode_count[ColorMode.ONOFF] = -1
                else:
                    color_mode_count.pop(ColorMode.ONOFF)
            if ColorMode.BRIGHTNESS in color_mode_count:
                if ColorMode.BRIGHTNESS in supported_color_modes:
                    color_mode_count[ColorMode.BRIGHTNESS] = 0
                else:
                    color_mode_count.pop(ColorMode.BRIGHTNESS)
            if color_mode_count:
                self._attr_color_mode = color_mode_count.most_common(1)[0][0]
            else:
                self._attr_color_mode = next(iter(supported_color_modes))

        self._attr_supported_features = LightEntityFeature(0)
        for support in find_state_attributes(states, ATTR_SUPPORTED_FEATURES):
            # Merge supported features by emulating support for every feature
            # we find.
            self._attr_supported_features |= support
        # Bitwise-and the supported features with the GroupedLight's features
        # so that we don't break in the future when a new feature is added.
        self._attr_supported_features &= SUPPORT_GROUP_LIGHT