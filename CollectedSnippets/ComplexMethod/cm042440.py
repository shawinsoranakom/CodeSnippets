def _update_active_connection_info(self):
    ipv4_address = ""
    metered = MeteredType.UNKNOWN

    conn_path, props = self._get_active_wifi_connection()

    if conn_path is not None and props is not None:
      # IPv4 address
      ip4config_path = props.get('Ip4Config', ('o', '/'))[1]

      if ip4config_path != "/":
        ip4config_addr = DBusAddress(ip4config_path, bus_name=NM, interface=NM_IP4_CONFIG_IFACE)
        address_data = self._router_main.send_and_get_reply(Properties(ip4config_addr).get('AddressData')).body[0][1]

        for entry in address_data:
          if 'address' in entry:
            ipv4_address = entry['address'][1]
            break

      # Metered status
      settings = self._get_connection_settings(conn_path)

      if len(settings) > 0:
        metered_prop = settings['connection'].get('metered', ('i', 0))[1]

        if metered_prop == MeteredType.YES:
          metered = MeteredType.YES
        elif metered_prop == MeteredType.NO:
          metered = MeteredType.NO

    self._ipv4_address = ipv4_address
    self._current_network_metered = metered