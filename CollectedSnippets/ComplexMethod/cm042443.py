def worker():
      try:
        lte_connection_path = self._get_lte_connection_path()
        if not lte_connection_path:
          cloudlog.warning("No LTE connection found")
          return

        settings = self._get_connection_settings(lte_connection_path)

        if len(settings) == 0:
          cloudlog.warning(f"Failed to get connection settings for {lte_connection_path}")
          return

        # Ensure dicts exist
        if 'gsm' not in settings:
          settings['gsm'] = {}
        if 'connection' not in settings:
          settings['connection'] = {}

        changes = False
        auto_config = apn == ""

        if settings['gsm'].get('auto-config', ('b', False))[1] != auto_config:
          cloudlog.warning(f'Changing gsm.auto-config to {auto_config}')
          settings['gsm']['auto-config'] = ('b', auto_config)
          changes = True

        if settings['gsm'].get('apn', ('s', ''))[1] != apn:
          cloudlog.warning(f'Changing gsm.apn to {apn}')
          settings['gsm']['apn'] = ('s', apn)
          changes = True

        if settings['gsm'].get('home-only', ('b', False))[1] == roaming:
          cloudlog.warning(f'Changing gsm.home-only to {not roaming}')
          settings['gsm']['home-only'] = ('b', not roaming)
          changes = True

        # Unknown means NetworkManager decides
        metered_int = int(MeteredType.UNKNOWN if metered else MeteredType.NO)
        if settings['connection'].get('metered', ('i', 0))[1] != metered_int:
          cloudlog.warning(f'Changing connection.metered to {metered_int}')
          settings['connection']['metered'] = ('i', metered_int)
          changes = True

        if changes:
          # Update the connection settings (temporary update)
          conn_addr = DBusAddress(lte_connection_path, bus_name=NM, interface=NM_CONNECTION_IFACE)
          reply = self._router_main.send_and_get_reply(new_method_call(conn_addr, 'UpdateUnsaved', 'a{sa{sv}}', (settings,)))

          if reply.header.message_type == MessageType.error:
            cloudlog.warning(f"Failed to update GSM settings: {reply}")
            return

          self._activate_modem_connection(lte_connection_path)
      except Exception as e:
        cloudlog.exception(f"Error updating GSM settings: {e}")