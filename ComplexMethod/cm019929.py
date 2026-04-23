async def test_availability(ismartgateapi_mock, hass: HomeAssistant) -> None:
    """Test availability."""
    closed_door_response = _mocked_ismartgate_closed_door_response()

    expected_attributes = {
        "device_class": "garage",
        "door_id": 1,
        "friendly_name": "mycontroller Door1",
        "is_closed": True,
        "supported_features": CoverEntityFeature.CLOSE | CoverEntityFeature.OPEN,
    }

    api = MagicMock(ISmartGateApi)
    api.async_info.return_value = closed_door_response
    ismartgateapi_mock.return_value = api

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        title="mycontroller",
        data={
            CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )
    config_entry.add_to_hass(hass)

    assert hass.states.get("cover.mycontroller_door1") is None
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1")
    assert (
        hass.states.get("cover.mycontroller_door1").attributes[ATTR_DEVICE_CLASS]
        == CoverDeviceClass.GARAGE
    )
    assert (
        hass.states.get("cover.mycontroller_door2").attributes[ATTR_DEVICE_CLASS]
        == CoverDeviceClass.GATE
    )

    api.async_info.side_effect = Exception("Error")

    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1").state == STATE_UNAVAILABLE

    api.async_info.side_effect = None
    api.async_info.return_value = closed_door_response
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.CLOSED,
        2: DoorStatus.CLOSED,
    }
    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1").state == CoverState.CLOSED
    assert (
        dict(hass.states.get("cover.mycontroller_door1").attributes)
        == expected_attributes
    )