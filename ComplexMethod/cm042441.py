def worker():
      if self._wifi_device is None:
        cloudlog.warning("No WiFi device found")
        return

      epoch = self._user_epoch

      dev_addr = DBusAddress(self._wifi_device, bus_name=NM, interface=NM_DEVICE_IFACE)
      dev_state = self._router_main.send_and_get_reply(Properties(dev_addr).get('State')).body[0][1]

      ssid: str | None = None
      status = ConnectStatus.DISCONNECTED
      if NMDeviceState.PREPARE <= dev_state <= NMDeviceState.SECONDARIES and dev_state != NMDeviceState.NEED_AUTH:
        status = ConnectStatus.CONNECTING
      elif dev_state == NMDeviceState.ACTIVATED:
        status = ConnectStatus.CONNECTED

      conn_path, _ = self._get_active_wifi_connection()
      if conn_path:
        ssid = next((s for s, p in self._connections.items() if p == conn_path), None)

      # Discard if user acted during DBus calls
      if self._user_epoch != epoch:
        return

      self._wifi_state = WifiState(ssid=ssid, status=status)