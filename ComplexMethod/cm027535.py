def _update_from_coordinator(self):
        current = self._tv.ambilight_current_configuration
        color = None

        if (cache_keys := _get_cache_keys(self._tv)) != self._cache_keys:
            self._cache_keys = cache_keys
            self._attr_effect_list = self._calculate_effect_list()
            self._attr_effect = str(self._calculate_effect())

        if current and current["isExpert"]:
            if settings := _get_settings(current):
                color = settings["color"]

        effect = AmbilightEffect.from_str(self._attr_effect)
        if effect.is_on(self._tv.powerstate):
            self._last_selected_effect = effect

        if effect.mode == EFFECT_EXPERT and color:
            self._attr_hs_color = (
                color["hue"] * 360.0 / 255.0,
                color["saturation"] * 100.0 / 255.0,
            )
            self._attr_brightness = color["brightness"]
        elif effect.mode == EFFECT_MODE and self._tv.ambilight_cached:
            hsv_h, hsv_s, hsv_v = color_RGB_to_hsv(
                *_average_pixels(self._tv.ambilight_cached)
            )
            self._attr_hs_color = hsv_h, hsv_s
            self._attr_brightness = hsv_v * 255.0 / 100.0
        else:
            self._attr_hs_color = None
            self._attr_brightness = None