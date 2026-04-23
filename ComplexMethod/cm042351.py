def get_network_type(self):
    try:
      primary_connection = self.nm.Get(NM, 'PrimaryConnection', dbus_interface=DBUS_PROPS, timeout=TIMEOUT)
      primary_connection = self.bus.get_object(NM, primary_connection)
      primary_type = primary_connection.Get(NM_CON_ACT, 'Type', dbus_interface=DBUS_PROPS, timeout=TIMEOUT)

      if primary_type == '802-3-ethernet':
        return NetworkType.ethernet
      elif primary_type == '802-11-wireless':
        return NetworkType.wifi
      else:
        active_connections = self.nm.Get(NM, 'ActiveConnections', dbus_interface=DBUS_PROPS, timeout=TIMEOUT)
        for conn in active_connections:
          c = self.bus.get_object(NM, conn)
          tp = c.Get(NM_CON_ACT, 'Type', dbus_interface=DBUS_PROPS, timeout=TIMEOUT)
          if tp == 'gsm':
            modem = self.get_modem()
            access_t = modem.Get(MM_MODEM, 'AccessTechnologies', dbus_interface=DBUS_PROPS, timeout=TIMEOUT)
            if access_t >= MM_MODEM_ACCESS_TECHNOLOGY_LTE:
              return NetworkType.cell4G
            elif access_t >= MM_MODEM_ACCESS_TECHNOLOGY_UMTS:
              return NetworkType.cell3G
            else:
              return NetworkType.cell2G
    except Exception:
      pass

    return NetworkType.none