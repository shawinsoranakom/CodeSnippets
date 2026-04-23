def render(self, rect: rl.Rectangle | None = None) -> bool | int | None:
    if rect is not None:
      self.set_rect(rect)

    self._update_state()

    if self._click_release_time is not None and rl.get_time() >= self._click_release_time:
      self._click_release_time = None

    if not self.is_visible:
      return None

    self._layout()
    ret = self._render(self._rect)

    if gui_app.show_touches:
      self._draw_debug_rect()

    # Keep track of whether mouse down started within the widget's rectangle
    if self.enabled and self.__was_awake:
      self._process_mouse_events()
    else:
      # TODO: ideally we emit release events when going disabled
      self.__is_pressed = [False] * MAX_TOUCH_SLOTS
      self.__tracking_is_pressed = [False] * MAX_TOUCH_SLOTS

    self.__was_awake = device.awake

    return ret