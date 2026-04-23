def _draw_network_item(self, rect, network: Network):
    spacing = 50
    ssid_rect = rl.Rectangle(rect.x, rect.y, rect.width - self.btn_width * 2, ITEM_HEIGHT)
    signal_icon_rect = rl.Rectangle(rect.x + rect.width - ICON_SIZE, rect.y + (ITEM_HEIGHT - ICON_SIZE) / 2, ICON_SIZE, ICON_SIZE)
    security_icon_rect = rl.Rectangle(signal_icon_rect.x - spacing - ICON_SIZE, rect.y + (ITEM_HEIGHT - ICON_SIZE) / 2, ICON_SIZE, ICON_SIZE)

    status_text = ""
    if self.state == UIState.CONNECTING and self._state_network:
      if self._state_network.ssid == network.ssid:
        self._networks_buttons[network.ssid].set_enabled(False)
        status_text = tr("CONNECTING...")
    elif self.state == UIState.FORGETTING and self._state_network:
      if self._state_network.ssid == network.ssid:
        self._networks_buttons[network.ssid].set_enabled(False)
        status_text = tr("FORGETTING...")
    elif network.security_type == SecurityType.UNSUPPORTED:
      self._networks_buttons[network.ssid].set_enabled(False)
    else:
      self._networks_buttons[network.ssid].set_enabled(True)

    self._networks_buttons[network.ssid].render(ssid_rect)

    if status_text:
      status_text_rect = rl.Rectangle(security_icon_rect.x - 410, rect.y, 410, ITEM_HEIGHT)
      gui_label(status_text_rect, status_text, font_size=48, alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER)
    else:
      # If the network is saved, show the "Forget" button
      if self._wifi_manager.is_connection_saved(network.ssid):
        forget_btn_rect = rl.Rectangle(
          security_icon_rect.x - self.btn_width - spacing,
          rect.y + (ITEM_HEIGHT - 80) / 2,
          self.btn_width,
          80,
        )
        self._forget_networks_buttons[network.ssid].render(forget_btn_rect)

    self._draw_status_icon(security_icon_rect, network)
    self._draw_signal_strength_icon(signal_icon_rect, network)