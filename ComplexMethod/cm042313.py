def _update_state(self):
    super()._update_state()

    if any((self._network_missing, self._is_connecting, self._is_connected, self._network_forgetting,
            self._network.security_type == SecurityType.UNSUPPORTED)):
      self.set_enabled(False)
      self._sub_label.set_color(rl.Color(255, 255, 255, int(255 * 0.585)))
      self._sub_label.set_font_weight(FontWeight.ROMAN)

      if self._network_forgetting:
        self.set_value("forgetting...")
      elif self._is_connecting:
        self.set_value("starting..." if self._network.is_tethering else "connecting...")
      elif self._is_connected:
        self.set_value("tethering" if self._network.is_tethering else "connected")
      elif self._network_missing:
        # after connecting/connected since NM will still attempt to connect/stay connected for a while
        self.set_value("not in range")
      else:
        self.set_value("unsupported")

    else:  # saved, wrong password, or unknown
      self.set_value("wrong password" if self._wrong_password else "connect")
      self.set_enabled(True)
      self._sub_label.set_color(rl.Color(255, 255, 255, int(255 * 0.9)))
      self._sub_label.set_font_weight(FontWeight.SEMI_BOLD)