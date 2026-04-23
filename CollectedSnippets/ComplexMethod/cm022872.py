async def test_enter_and_exit(
    hass: HomeAssistant, locative_client: TestClient, webhook_id: str
) -> None:
    """Test when there is a known zone."""
    url = f"/api/webhook/{webhook_id}"

    data = {
        "latitude": 40.7855,
        "longitude": -111.7367,
        "device": "123",
        "id": "Home",
        "trigger": "enter",
    }

    # Enter the Home
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    assert state_name == "home"

    data["id"] = "HOME"
    data["trigger"] = "exit"

    # Exit Home
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    assert state_name == "not_home"

    data["id"] = "hOmE"
    data["trigger"] = "enter"

    # Enter Home again
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    assert state_name == "home"

    data["trigger"] = "exit"

    # Exit Home
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    assert state_name == "not_home"

    data["id"] = "work"
    data["trigger"] = "enter"

    # Enter Work
    req = await locative_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    assert state_name == "work"