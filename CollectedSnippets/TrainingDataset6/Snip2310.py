def test_websocket_dependency_after_yield():
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_text()
        assert data == "foo"
        data = websocket.receive_text()
        assert data == "bar"
        data = websocket.receive_text()
        assert data == "baz"