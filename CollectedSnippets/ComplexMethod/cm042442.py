def worker():
      with self._scan_lock:
        if self._wifi_device is None:
          cloudlog.warning("No WiFi device found")
          return

        # NOTE: AccessPoints property may exclude hidden APs (use GetAllAccessPoints method if needed)
        wifi_addr = DBusAddress(self._wifi_device, NM, interface=NM_WIRELESS_IFACE)
        wifi_props_reply = self._router_main.send_and_get_reply(Properties(wifi_addr).get_all())
        if wifi_props_reply.header.message_type == MessageType.error:
          cloudlog.warning(f"Failed to get WiFi properties: {wifi_props_reply}")
          return

        ap_paths = wifi_props_reply.body[0].get('AccessPoints', ('ao', []))[1]

        aps: dict[str, list[AccessPoint]] = {}

        for ap_path in ap_paths:
          ap_addr = DBusAddress(ap_path, NM, interface=NM_ACCESS_POINT_IFACE)
          ap_props = self._router_main.send_and_get_reply(Properties(ap_addr).get_all())

          # some APs have been seen dropping off during iteration
          if ap_props.header.message_type == MessageType.error:
            cloudlog.warning(f"Failed to get AP properties for {ap_path}")
            continue

          try:
            ap = AccessPoint.from_dbus(ap_props.body[0], ap_path)
            if ap.ssid == "":
              continue

            if ap.ssid not in aps:
              aps[ap.ssid] = []

            aps[ap.ssid].append(ap)
          except Exception:
            # catch all for parsing errors
            cloudlog.exception(f"Failed to parse AP properties for {ap_path}")

        self._networks = [Network.from_dbus(ssid, ap_list, ssid == self._tethering_ssid) for ssid, ap_list in aps.items()]
        self._update_active_connection_info()
        self._enqueue_callbacks(self._networks_updated, self.networks)