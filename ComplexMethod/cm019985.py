async def test_invalid_or_missing_data(
    mock_device_tracker_conf: list[legacy.Device], meraki_client
) -> None:
    """Test validator with invalid or missing data."""
    req = await meraki_client.get(URL)
    text = await req.text()
    assert req.status == HTTPStatus.OK
    assert text == "validator"

    req = await meraki_client.post(URL, data=b"invalid")
    text = await req.json()
    assert req.status == HTTPStatus.BAD_REQUEST
    assert text["message"] == "Invalid JSON"

    req = await meraki_client.post(URL, data=b"{}")
    text = await req.json()
    assert req.status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert text["message"] == "No secret"

    data = {"version": "1.0", "secret": "secret"}
    req = await meraki_client.post(URL, data=json.dumps(data))
    text = await req.json()
    assert req.status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert text["message"] == "Invalid version"

    data = {"version": "2.0", "secret": "invalid"}
    req = await meraki_client.post(URL, data=json.dumps(data))
    text = await req.json()
    assert req.status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert text["message"] == "Invalid secret"

    data = {"version": "2.0", "secret": "secret", "type": "InvalidType"}
    req = await meraki_client.post(URL, data=json.dumps(data))
    text = await req.json()
    assert req.status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert text["message"] == "Invalid device type"

    data = {
        "version": "2.0",
        "secret": "secret",
        "type": "BluetoothDevicesSeen",
        "data": {"observations": []},
    }
    req = await meraki_client.post(URL, data=json.dumps(data))
    assert req.status == HTTPStatus.OK