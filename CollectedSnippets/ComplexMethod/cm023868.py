async def test_discover_full_state(hue_client: TestClient) -> None:
    """Test the discovery of full state."""
    result = await hue_client.get(f"/api/{HUE_API_USERNAME}")

    assert result.status == HTTPStatus.OK
    assert CONTENT_TYPE_JSON in result.headers["content-type"]

    result_json = await result.json()

    # Make sure array has correct content
    assert "lights" in result_json
    assert "lights" not in result_json["config"]
    assert "config" in result_json
    assert "config" not in result_json["lights"]

    lights_json = result_json["lights"]
    config_json = result_json["config"]

    # Make sure array is correct size
    assert len(result_json) == 2
    assert len(config_json) == 7
    assert len(lights_json) >= 1
    assert "name" in config_json

    # Make sure the config wrapper added to the config is there
    assert "mac" in config_json
    assert "00:00:00:00:00:00" in config_json["mac"]

    # Make sure the correct version in config
    assert "swversion" in config_json
    assert "01003542" in config_json["swversion"]

    # Make sure the api version is correct
    assert "apiversion" in config_json
    assert "1.17.0" in config_json["apiversion"]

    # Make sure the correct username in config
    assert "whitelist" in config_json
    assert HUE_API_USERNAME in config_json["whitelist"]
    assert "name" in config_json["whitelist"][HUE_API_USERNAME]
    assert "HASS BRIDGE" in config_json["whitelist"][HUE_API_USERNAME]["name"]

    # Make sure the correct ip in config
    assert "ipaddress" in config_json
    assert "127.0.0.1:8300" in config_json["ipaddress"]

    # Make sure the device announces a link button
    assert "linkbutton" in config_json
    assert config_json["linkbutton"] is True