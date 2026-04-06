def test_websocket_dependency_after_yield_broken():
    with pytest.raises(ValueError, match="Session closed"):
        with client.websocket_connect("/ws-broken"):
            pass