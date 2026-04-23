def _update_buttons(self, re_sort: bool = False):
    # Update existing buttons, add new ones to the end
    existing = {btn.network.ssid: btn for btn in self._scroller.items if isinstance(btn, WifiButton)}

    for network in self._networks.values():
      if network.ssid in existing:
        existing[network.ssid].update_network(network)
      else:
        btn = WifiButton(network, self._wifi_manager)
        btn.set_click_callback(lambda ssid=network.ssid: self._connect_to_network(ssid))
        self._scroller.add_widget(btn)

    if re_sort:
      # Remove stale buttons and sort to match scan order, preserving eager state
      btn_map = {btn.network.ssid: btn for btn in self._scroller.items if isinstance(btn, WifiButton)}
      self._scroller.items[:] = [btn_map[ssid] for ssid in self._networks if ssid in btn_map]
    else:
      # Mark networks no longer in scan results (display handled by _update_state)
      for btn in self._scroller.items:
        if isinstance(btn, WifiButton) and btn.network.ssid not in self._networks:
          btn.set_network_missing(True)

    # Keep scanning button at the end
    items = self._scroller.items
    if self._scanning_btn in items:
      items.append(items.pop(items.index(self._scanning_btn)))
    else:
      self._scroller.add_widget(self._scanning_btn)