def _update_state(self):
    super()._update_state()

    # Update wi-fi button with ssid and ip address
    # TODO: make sure we handle hidden ssids
    wifi_state = self._wifi_manager.wifi_state
    display_network = next((n for n in self._wifi_manager.networks if n.ssid == wifi_state.ssid), None)
    if wifi_state.status == ConnectStatus.CONNECTING:
      self.set_text(normalize_ssid(wifi_state.ssid or "wi-fi"))
      self.set_value("starting" if self._wifi_manager.is_tethering_active() else "connecting...")
    elif wifi_state.status == ConnectStatus.CONNECTED:
      self.set_text(normalize_ssid(wifi_state.ssid or "wi-fi"))
      self.set_value(self._wifi_manager.ipv4_address or "obtaining IP...")
    else:
      display_network = None
      self.set_text("wi-fi")
      self.set_value("not connected")

    if display_network is not None:
      strength = WifiIcon.get_strength_icon_idx(display_network.strength)
      self.set_icon(self._wifi_full_txt if strength == 2 else self._wifi_medium_txt if strength == 1 else self._wifi_low_txt)
      self._draw_lock = display_network.security_type not in (SecurityType.OPEN, SecurityType.UNSUPPORTED)
    elif self._wifi_manager.is_tethering_active():
      # takes a while to get Network
      self.set_icon(self._wifi_full_txt)
      self._draw_lock = True
    else:
      self.set_icon(self._wifi_slash_txt)
      self._draw_lock = False