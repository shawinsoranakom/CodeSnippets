def _handle_mouse_release(self, mouse_pos: MousePos):
    if not self._did_long_press:
      relative_x = mouse_pos.x - self.rect.x
      has_alerts = self._alert_count_callback and self._alert_count_callback() > 0
      if relative_x < SETTINGS_ZONE_WIDTH:
        if self._on_settings_click:
          self._on_settings_click()
      elif has_alerts and relative_x > self.rect.width - ALERTS_ZONE_WIDTH:
        if self._on_alerts_click:
          self._on_alerts_click()
    self._did_long_press = False