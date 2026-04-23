def get_network_info(self):
    if self.get_device_type() == "mici":
      return None
    try:
      modem = self.get_modem()
      info = modem.Command("AT+QNWINFO", math.ceil(TIMEOUT), dbus_interface=MM_MODEM, timeout=TIMEOUT)
      extra = modem.Command('AT+QENG="servingcell"', math.ceil(TIMEOUT), dbus_interface=MM_MODEM, timeout=TIMEOUT)
      state = modem.Get(MM_MODEM, 'State', dbus_interface=DBUS_PROPS, timeout=TIMEOUT)
    except Exception:
      return None

    if info and info.startswith('+QNWINFO: '):
      info = info.replace('+QNWINFO: ', '').replace('"', '').split(',')
      extra = "" if extra is None else extra.replace('+QENG: "servingcell",', '').replace('"', '')
      state = "" if state is None else MM_MODEM_STATE(state).name

      if len(info) != 4:
        return None

      technology, operator, band, channel = info

      return({
        'technology': technology,
        'operator': operator,
        'band': band,
        'channel': int(channel),
        'extra': extra,
        'state': state,
      })
    else:
      return None