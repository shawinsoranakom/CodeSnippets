def _handle_state_change(self, new_state: int, prev_state: int, change_reason: int):
    # Thread safety: _wifi_state is read/written by both the monitor thread (this handler)
    # and the main thread (_set_connecting via connect/activate). PREPARE/CONFIG and ACTIVATED
    # have a read-then-write pattern with a slow DBus call in between — if _set_connecting
    # runs mid-call, the handler would overwrite the user's newer state with stale data.
    #
    # The _user_epoch counter solves this without locks. _set_connecting increments the epoch
    # on every user action. Handlers snapshot the epoch before their DBus call and compare
    # after: if it changed, a user action occurred during the call and the stale result is
    # discarded. Combined with deterministic fixes (skip DBus lookup when ssid already set,
    # DEACTIVATING clears CONNECTED on CONNECTION_REMOVED, CONNECTION_REMOVED guard),
    # all known race windows are closed.

    # TODO: Handle (FAILED, SSID_NOT_FOUND) and emit for UI to show error
    #  Happens when network drops off after starting connection

    if new_state == NMDeviceState.DISCONNECTED:
      if change_reason == NMDeviceStateReason.NEW_ACTIVATION:
        return

      # Guard: forget A while connecting to B fires CONNECTION_REMOVED. Don't clear B's state
      # if B is still a known connection. If B hasn't arrived in _connections yet (late
      # NewConnection), state clears here but PREPARE recovers via DBus lookup.
      if (change_reason == NMDeviceStateReason.CONNECTION_REMOVED and self._wifi_state.ssid and
        self._wifi_state.ssid in self._connections):
        return

      self._set_connecting(None)

    elif new_state in (NMDeviceState.PREPARE, NMDeviceState.CONFIG):
      epoch = self._user_epoch

      if self._wifi_state.ssid is not None:
        self._wifi_state = replace(self._wifi_state, status=ConnectStatus.CONNECTING)
        return

      # Auto-connection when NetworkManager connects to known networks on its own (ssid=None): look up ssid from NM
      wifi_state = replace(self._wifi_state, status=ConnectStatus.CONNECTING)

      conn_path, _ = self._get_active_wifi_connection(self._conn_monitor)

      # Discard if user acted during DBus call
      if self._user_epoch != epoch:
        return

      if conn_path is None:
        cloudlog.warning("Failed to get active wifi connection during PREPARE/CONFIG state")
      else:
        wifi_state = replace(wifi_state, ssid=next((s for s, p in self._connections.items() if p == conn_path), None))

      self._wifi_state = wifi_state

    # BAD PASSWORD
    # - strong network rejects with NEED_AUTH+SUPPLICANT_DISCONNECT
    # - weak/gone network fails with FAILED+NO_SECRETS
    # TODO: sometimes on PC it's observed no future signals are fired if mouse is held down blocking wrong password dialog
    elif ((new_state == NMDeviceState.NEED_AUTH and change_reason == NMDeviceStateReason.SUPPLICANT_DISCONNECT
           and prev_state == NMDeviceState.CONFIG) or
          (new_state == NMDeviceState.FAILED and change_reason == NMDeviceStateReason.NO_SECRETS)):

      # prev_state guard: real auth failures come from CONFIG (supplicant handshake).
      # Stale NEED_AUTH from a prior connection during network switching arrives with
      # prev_state=DISCONNECTED and must be ignored to avoid a false wrong-password callback.
      if self._wifi_state.ssid:
        self._enqueue_callbacks(self._need_auth, self._wifi_state.ssid)
        self._set_connecting(None)

    elif new_state in (NMDeviceState.NEED_AUTH, NMDeviceState.IP_CONFIG, NMDeviceState.IP_CHECK,
                       NMDeviceState.SECONDARIES, NMDeviceState.FAILED):
      pass

    elif new_state == NMDeviceState.ACTIVATED:
      # Note that IP address from Ip4Config may not be propagated immediately and could take until the next scan results
      epoch = self._user_epoch
      wifi_state = replace(self._wifi_state, status=ConnectStatus.CONNECTED)

      conn_path, _ = self._get_active_wifi_connection(self._conn_monitor)

      # Discard if user acted during DBus call
      if self._user_epoch != epoch:
        return

      if conn_path is None:
        cloudlog.warning("Failed to get active wifi connection during ACTIVATED state")
      else:
        wifi_state = replace(wifi_state, ssid=next((s for s, p in self._connections.items() if p == conn_path), None))

      self._wifi_state = wifi_state
      self._enqueue_callbacks(self._activated)
      self._update_active_connection_info()

      # Persist volatile connections (created by AddAndActivateConnection2) to disk
      if conn_path is not None:
        conn_addr = DBusAddress(conn_path, bus_name=NM, interface=NM_CONNECTION_IFACE)
        save_reply = self._conn_monitor.send_and_get_reply(new_method_call(conn_addr, 'Save'))
        if save_reply.header.message_type == MessageType.error:
          cloudlog.warning(f"Failed to persist connection to disk: {save_reply}")

    elif new_state == NMDeviceState.DEACTIVATING:
      # Must clear state when forgetting the currently connected network so the UI
      # doesn't flash "connected" after the eager "forgetting..." state resets
      # (the forgotten callback fires between DEACTIVATING and DISCONNECTED).
      # Only clear CONNECTED — CONNECTING must be preserved for forget-A-connect-B.
      if change_reason == NMDeviceStateReason.CONNECTION_REMOVED and self._wifi_state.status == ConnectStatus.CONNECTED:
        self._set_connecting(None)