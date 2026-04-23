async def test_extra_js(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    mock_http_client_with_extra_js: TestClient,
) -> None:
    """Test that extra javascript is loaded."""

    async def get_response():
        resp = await mock_http_client_with_extra_js.get("")
        assert resp.status == 200
        assert "cache-control" not in resp.headers

        return await resp.text()

    text = await get_response()
    assert '"/local/my_module.js"' in text
    assert '"/local/my_es5.js"' in text

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "frontend/subscribe_extra_js"})
    msg = await client.receive_json()

    assert msg["success"] is True
    subscription_id = msg["id"]

    # Test dynamically adding and removing extra javascript
    add_extra_js_url(hass, "/local/my_module_2.js", False)
    add_extra_js_url(hass, "/local/my_es5_2.js", True)
    text = await get_response()
    assert '"/local/my_module_2.js"' in text
    assert '"/local/my_es5_2.js"' in text

    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["event"] == {
        "change_type": "added",
        "item": {"type": "module", "url": "/local/my_module_2.js"},
    }
    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["event"] == {
        "change_type": "added",
        "item": {"type": "es5", "url": "/local/my_es5_2.js"},
    }

    remove_extra_js_url(hass, "/local/my_module_2.js", False)
    remove_extra_js_url(hass, "/local/my_es5_2.js", True)
    text = await get_response()
    assert '"/local/my_module_2.js"' not in text
    assert '"/local/my_es5_2.js"' not in text

    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["event"] == {
        "change_type": "removed",
        "item": {"type": "module", "url": "/local/my_module_2.js"},
    }
    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["event"] == {
        "change_type": "removed",
        "item": {"type": "es5", "url": "/local/my_es5_2.js"},
    }

    # Remove again should not raise
    remove_extra_js_url(hass, "/local/my_module_2.js", False)
    remove_extra_js_url(hass, "/local/my_es5_2.js", True)
    text = await get_response()
    assert '"/local/my_module_2.js"' not in text
    assert '"/local/my_es5_2.js"' not in text

    # safe mode
    hass.config.safe_mode = True
    text = await get_response()
    assert '"/local/my_module.js"' not in text
    assert '"/local/my_es5.js"' not in text

    # Test dynamically adding extra javascript
    add_extra_js_url(hass, "/local/my_module_2.js", False)
    add_extra_js_url(hass, "/local/my_es5_2.js", True)
    text = await get_response()
    assert '"/local/my_module_2.js"' not in text
    assert '"/local/my_es5_2.js"' not in text