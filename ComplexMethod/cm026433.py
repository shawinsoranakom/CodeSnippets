def get_registered_script(self, **kwargs) -> tuple[str, dict]:
        """Get registered script for turn_on."""
        common_params = {}

        if ATTR_BRIGHTNESS in kwargs:
            common_params["brightness"] = kwargs[ATTR_BRIGHTNESS]

        if ATTR_TRANSITION in kwargs and self._supports_transition is True:
            common_params["transition"] = kwargs[ATTR_TRANSITION]

        if (
            ATTR_COLOR_TEMP_KELVIN in kwargs
            and (script := CONF_TEMPERATURE_ACTION) in self._action_scripts
        ):
            kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
            common_params[ATTR_COLOR_TEMP_KELVIN] = kelvin
            common_params[ATTR_COLOR_TEMP] = (
                color_util.color_temperature_kelvin_to_mired(kelvin)
            )

            return (script, common_params)

        if (
            ATTR_EFFECT in kwargs
            and (script := CONF_EFFECT_ACTION) in self._action_scripts
        ):
            assert self._attr_effect_list is not None
            effect = kwargs[ATTR_EFFECT]
            if (
                self._attr_effect_list is not None
                and effect not in self._attr_effect_list
            ):
                _LOGGER.error(
                    "Received invalid effect: %s for entity %s. Expected one of: %s",
                    effect,
                    self.entity_id,
                    self._attr_effect_list,
                )

            common_params["effect"] = effect

            return (script, common_params)

        if (
            ATTR_HS_COLOR in kwargs
            and (script := CONF_HS_ACTION) in self._action_scripts
        ):
            hs_value = kwargs[ATTR_HS_COLOR]
            common_params["hs"] = hs_value
            common_params["h"] = int(hs_value[0])
            common_params["s"] = int(hs_value[1])

            return (script, common_params)

        if (
            ATTR_RGBWW_COLOR in kwargs
            and (script := CONF_RGBWW_ACTION) in self._action_scripts
        ):
            rgbww_value = kwargs[ATTR_RGBWW_COLOR]
            common_params["rgbww"] = rgbww_value
            common_params["rgb"] = (
                int(rgbww_value[0]),
                int(rgbww_value[1]),
                int(rgbww_value[2]),
            )
            common_params["r"] = int(rgbww_value[0])
            common_params["g"] = int(rgbww_value[1])
            common_params["b"] = int(rgbww_value[2])
            common_params["cw"] = int(rgbww_value[3])
            common_params["ww"] = int(rgbww_value[4])

            return (script, common_params)

        if (
            ATTR_RGBW_COLOR in kwargs
            and (script := CONF_RGBW_ACTION) in self._action_scripts
        ):
            rgbw_value = kwargs[ATTR_RGBW_COLOR]
            common_params["rgbw"] = rgbw_value
            common_params["rgb"] = (
                int(rgbw_value[0]),
                int(rgbw_value[1]),
                int(rgbw_value[2]),
            )
            common_params["r"] = int(rgbw_value[0])
            common_params["g"] = int(rgbw_value[1])
            common_params["b"] = int(rgbw_value[2])
            common_params["w"] = int(rgbw_value[3])

            return (script, common_params)

        if (
            ATTR_RGB_COLOR in kwargs
            and (script := CONF_RGB_ACTION) in self._action_scripts
        ):
            rgb_value = kwargs[ATTR_RGB_COLOR]
            common_params["rgb"] = rgb_value
            common_params["r"] = int(rgb_value[0])
            common_params["g"] = int(rgb_value[1])
            common_params["b"] = int(rgb_value[2])

            return (script, common_params)

        if (
            ATTR_BRIGHTNESS in kwargs
            and (script := CONF_LEVEL_ACTION) in self._action_scripts
        ):
            return (script, common_params)

        return (CONF_ON_ACTION, common_params)