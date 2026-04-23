async def test_is_json() -> None:
    """Test is_json method."""

    # Valid JSON values
    assert is_json("{}")
    assert is_json('{ "simple":"json" }')
    assert is_json(json.dumps(DATA_WIFI_GET_GLOBAL_CONFIG))
    assert is_json(json.dumps(DATA_LAN_GET_HOSTS_LIST_MODE_BRIDGE))

    # Not valid JSON values
    assert not is_json(None)
    assert not is_json("")
    assert not is_json("XXX")
    assert not is_json("{XXX}")