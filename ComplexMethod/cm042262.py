def _update_brightness(self):
    clipped_brightness = self._offroad_brightness

    if ui_state.started and ui_state.light_sensor >= 0:
      clipped_brightness = ui_state.light_sensor

      # CIE 1931 - https://www.photonstophotos.net/GeneralTopics/Exposure/Psychometric_Lightness_and_Gamma.htm
      if clipped_brightness <= 8:
        clipped_brightness = clipped_brightness / 903.3
      else:
        clipped_brightness = ((clipped_brightness + 16.0) / 116.0) ** 3.0

      clipped_brightness = float(np.interp(clipped_brightness, [0, 1], [30, 100]))

    brightness = round(self._brightness_filter.update(clipped_brightness))
    if not self._awake:
      brightness = 0

    if brightness != self._last_brightness:
      if self._brightness_thread is None or not self._brightness_thread.is_alive():
        self._brightness_thread = threading.Thread(target=HARDWARE.set_screen_brightness, args=(brightness,))
        self._brightness_thread.start()
        self._last_brightness = brightness