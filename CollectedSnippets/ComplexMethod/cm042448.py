def test_forget_A_connect_B_late_new_connection(self, mocker):
    """Forget A, connect B: NewConnection for B arrives AFTER DISCONNECTED.

    This is the worst-case race: B isn't in _connections when DISCONNECTED fires,
    so the guard can't protect it and state clears. PREPARE must recover by doing
    the DBus lookup (ssid is None at that point).

    Signal order:
      1. User: _set_connecting("B"), forget("A") removes A from _connections
      2. DEACTIVATING(CONNECTION_REMOVED) — B NOT in _connections, should be no-op
      3. DISCONNECTED(CONNECTION_REMOVED) — B STILL NOT in _connections, clears state
      4. NewConnection for B arrives late → _connections["B"] = ...
      5. PREPARE (ssid=None, so DBus lookup recovers) → CONFIG → ACTIVATED
    """
    wm = _make_wm(mocker, connections={"A": "/path/A"})
    wm._wifi_state = WifiState(ssid="A", status=ConnectStatus.CONNECTED)

    wm._set_connecting("B")
    del wm._connections["A"]

    fire(wm, NMDeviceState.DEACTIVATING, prev_state=NMDeviceState.ACTIVATED,
         reason=NMDeviceStateReason.CONNECTION_REMOVED)
    assert wm._wifi_state.ssid == "B"
    assert wm._wifi_state.status == ConnectStatus.CONNECTING

    fire(wm, NMDeviceState.DISCONNECTED, prev_state=NMDeviceState.DEACTIVATING,
         reason=NMDeviceStateReason.CONNECTION_REMOVED)
    # B not in _connections yet, so state clears — this is the known edge case
    assert wm._wifi_state.ssid is None
    assert wm._wifi_state.status == ConnectStatus.DISCONNECTED

    # NewConnection arrives late
    wm._connections["B"] = "/path/B"
    wm._get_active_wifi_connection.return_value = ("/path/B", {})

    # PREPARE recovers: ssid is None so it looks up from DBus
    fire(wm, NMDeviceState.PREPARE)
    assert wm._wifi_state.ssid == "B"
    assert wm._wifi_state.status == ConnectStatus.CONNECTING

    fire(wm, NMDeviceState.CONFIG)
    fire_wpa_connect(wm)
    assert wm._wifi_state.status == ConnectStatus.CONNECTED
    assert wm._wifi_state.ssid == "B"