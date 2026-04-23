def test_forget_while_connecting(self, mocker):
    """Forget the network we're currently connecting to (not yet ACTIVATED).

    Confirmed on device: connected to unifi, tapped Shane's iPhone, then forgot
    Shane's iPhone while at CONFIG. NM auto-connected to unifi afterward.

    Real device sequence (switching then forgetting mid-connection):
      DEACTIVATING(ACTIVATED, NEW_ACTIVATION) → DISCONNECTED(DEACTIVATING, NEW_ACTIVATION)
      → PREPARE → CONFIG → NEED_AUTH(CONFIG, NONE) → PREPARE(NEED_AUTH) → CONFIG
      → DEACTIVATING(CONFIG, CONNECTION_REMOVED)                ← forget at CONFIG
      → DISCONNECTED(DEACTIVATING, CONNECTION_REMOVED)
      → PREPARE → CONFIG → ... → ACTIVATED                     ← NM auto-connects to other saved network

    Note: DEACTIVATING fires from CONFIG (not ACTIVATED). wifi_state.status is
    CONNECTING, so the DEACTIVATING handler is a no-op. DISCONNECTED clears state
    (ssid removed from _connections by ConnectionRemoved), then PREPARE recovers
    via DBus lookup for the auto-connect.
    """
    wm = _make_wm(mocker, connections={"A": "/path/A", "Other": "/path/other"})
    wm._get_active_wifi_connection.return_value = ("/path/other", {})

    wm._set_connecting("A")

    fire(wm, NMDeviceState.PREPARE)
    fire(wm, NMDeviceState.CONFIG)
    assert wm._wifi_state.ssid == "A"
    assert wm._wifi_state.status == ConnectStatus.CONNECTING

    # User forgets A: ConnectionRemoved processed first, then state changes
    del wm._connections["A"]

    fire(wm, NMDeviceState.DEACTIVATING, prev_state=NMDeviceState.CONFIG,
         reason=NMDeviceStateReason.CONNECTION_REMOVED)
    assert wm._wifi_state.ssid == "A"
    assert wm._wifi_state.status == ConnectStatus.CONNECTING  # DEACTIVATING preserves CONNECTING

    fire(wm, NMDeviceState.DISCONNECTED, prev_state=NMDeviceState.DEACTIVATING,
         reason=NMDeviceStateReason.CONNECTION_REMOVED)
    assert wm._wifi_state.ssid is None
    assert wm._wifi_state.status == ConnectStatus.DISCONNECTED

    # NM auto-connects to another saved network
    fire(wm, NMDeviceState.PREPARE)
    assert wm._wifi_state.ssid == "Other"
    assert wm._wifi_state.status == ConnectStatus.CONNECTING

    fire(wm, NMDeviceState.CONFIG)
    fire_wpa_connect(wm)
    assert wm._wifi_state.status == ConnectStatus.CONNECTED
    assert wm._wifi_state.ssid == "Other"