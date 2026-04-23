def _monitor_state(self):
    # Filter for signals
    rules = (
      MatchRule(
        type="signal",
        interface=NM_DEVICE_IFACE,
        member="StateChanged",
        path=self._wifi_device,
      ),
      MatchRule(
        type="signal",
        interface=NM_SETTINGS_IFACE,
        member="NewConnection",
        path=NM_SETTINGS_PATH,
      ),
      MatchRule(
        type="signal",
        interface=NM_SETTINGS_IFACE,
        member="ConnectionRemoved",
        path=NM_SETTINGS_PATH,
      ),
      MatchRule(
        type="signal",
        interface=NM_PROPERTIES_IFACE,
        member="PropertiesChanged",
        path=self._wifi_device,
      ),
    )

    for rule in rules:
      self._conn_monitor.send_and_get_reply(message_bus.AddMatch(rule))

    with (self._conn_monitor.filter(rules[0], bufsize=SIGNAL_QUEUE_SIZE) as state_q,
          self._conn_monitor.filter(rules[1], bufsize=SIGNAL_QUEUE_SIZE) as new_conn_q,
          self._conn_monitor.filter(rules[2], bufsize=SIGNAL_QUEUE_SIZE) as removed_conn_q,
          self._conn_monitor.filter(rules[3], bufsize=SIGNAL_QUEUE_SIZE) as props_q):
      while not self._exit:
        try:
          self._conn_monitor.recv_messages(timeout=1)
        except TimeoutError:
          continue

        # Connection added/removed
        while len(removed_conn_q):
          conn_path = removed_conn_q.popleft().body[0]
          self._connection_removed(conn_path)
        while len(new_conn_q):
          conn_path = new_conn_q.popleft().body[0]
          self._new_connection(conn_path)

        # PropertiesChanged on wifi device (LastScan = scan complete)
        while len(props_q):
          iface, changed, _ = props_q.popleft().body
          if iface == NM_WIRELESS_IFACE and 'LastScan' in changed:
            self._update_networks()

        # Device state changes
        while len(state_q):
          new_state, previous_state, change_reason = state_q.popleft().body

          self._handle_state_change(new_state, previous_state, change_reason)