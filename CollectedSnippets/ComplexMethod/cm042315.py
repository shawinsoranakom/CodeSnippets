def _move_network_to_front(self, ssid: str | None, scroll: bool = False):
    # Move connecting/connected network to the front with animation
    front_btn_idx = next((i for i, btn in enumerate(self._scroller.items)
                          if isinstance(btn, WifiButton) and
                          btn.network.ssid == ssid), None) if ssid else None

    if front_btn_idx is not None and front_btn_idx > 0:
      self._scroller.move_item(front_btn_idx, 0)

      if scroll:
        # Scroll to the new position of the network
        self._scroller.scroll_to(self._scroller.scroll_panel.get_offset(), smooth=True)