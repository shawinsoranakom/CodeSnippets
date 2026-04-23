async def test_missing_data(locative_client: TestClient, webhook_id: str) -> None:
    """Test missing data."""
    url = f"/api/webhook/{webhook_id}"

    data = {
        "latitude": 1.0,
        "longitude": 1.1,
        "device": "123",
        "id": "Home",
        "trigger": "enter",
    }

    # No data
    req = await locative_client.post(url)
    assert req.status == HTTPStatus.UNPROCESSABLE_ENTITY

    # No latitude
    copy = data.copy()
    del copy["latitude"]
    req = await locative_client.post(url, data=copy)
    assert req.status == HTTPStatus.UNPROCESSABLE_ENTITY

    # No device
    copy = data.copy()
    del copy["device"]
    req = await locative_client.post(url, data=copy)
    assert req.status == HTTPStatus.UNPROCESSABLE_ENTITY

    # No location
    copy = data.copy()
    del copy["id"]
    req = await locative_client.post(url, data=copy)
    assert req.status == HTTPStatus.UNPROCESSABLE_ENTITY

    # No trigger
    copy = data.copy()
    del copy["trigger"]
    req = await locative_client.post(url, data=copy)
    assert req.status == HTTPStatus.UNPROCESSABLE_ENTITY

    # Test message
    copy = data.copy()
    copy["trigger"] = "test"
    req = await locative_client.post(url, data=copy)
    assert req.status == HTTPStatus.OK

    # Test message, no location
    copy = data.copy()
    copy["trigger"] = "test"
    del copy["id"]
    req = await locative_client.post(url, data=copy)
    assert req.status == HTTPStatus.OK

    # Unknown trigger
    copy = data.copy()
    copy["trigger"] = "foobar"
    req = await locative_client.post(url, data=copy)
    assert req.status == HTTPStatus.UNPROCESSABLE_ENTITY