def _nav_stack_tick(self):
    # Only run tick when this page or its WiFi UI is on the stack
    if gui_app.get_active_widget() is not self and not gui_app.widget_in_stack(self._wifi_ui):
      self._wifi_manager.process_callbacks()
      return

    # Check network state before processing callbacks so forgetting flag
    # is still set on the frame the forgotten callback fires
    has_internet = self._has_internet
    wifi_connected = self._wifi_manager.wifi_state.status == ConnectStatus.CONNECTED

    self._continue_button.set_visible(has_internet)
    self._waiting_button.set_visible(not has_internet)

    # TODO: fire show/hide events on visibility changes
    if not has_internet:
      self._pending_continue_grow_animation = False
      self._waiting_button.set_text("waiting for\ninternet..." if wifi_connected else "connect to\ncontinue")

    self._wifi_manager.process_callbacks()

    # Dismiss WiFi UI and scroll on WiFi connect or internet gain
    if (has_internet and not self._prev_has_internet) or (wifi_connected and not self._prev_wifi_connected):
      # TODO: cancel if connect is transient
      self._pending_has_internet_scroll = rl.get_time()

    self._prev_has_internet = has_internet
    self._prev_wifi_connected = wifi_connected

    if self._pending_has_internet_scroll is not None:
      # Scrolls over to continue button, then grows once in view
      elapsed = rl.get_time() - self._pending_has_internet_scroll
      if elapsed > 0.7 or gui_app.get_active_widget() is self:  # instant scroll + grow if not popping
        # Animate WifiUi down first before scroll
        self._pending_has_internet_scroll = None
        gui_app.pop_widgets_to(self, self._scroll_to_end_and_grow)