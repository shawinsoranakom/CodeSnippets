async def test_open_close_update(gogogate2api_mock, hass: HomeAssistant) -> None:
    """Test open and close and data update."""

    def info_response(door_status: DoorStatus) -> GogoGate2InfoResponse:
        return GogoGate2InfoResponse(
            user="user1",
            gogogatename="gogogatename0",
            model="",
            apiversion="",
            remoteaccessenabled=False,
            remoteaccess="abc123.blah.blah",
            firmwareversion="",
            apicode="",
            door1=GogoGate2Door(
                door_id=1,
                permission=True,
                name="Door1",
                gate=False,
                mode=DoorMode.GARAGE,
                status=door_status,
                sensor=True,
                sensorid=None,
                camera=False,
                events=2,
                temperature=None,
                voltage=40,
            ),
            door2=GogoGate2Door(
                door_id=2,
                permission=True,
                name=None,
                gate=True,
                mode=DoorMode.GARAGE,
                status=DoorStatus.UNDEFINED,
                sensor=True,
                sensorid=None,
                camera=False,
                events=0,
                temperature=None,
                voltage=40,
            ),
            door3=GogoGate2Door(
                door_id=3,
                permission=True,
                name=None,
                gate=False,
                mode=DoorMode.GARAGE,
                status=DoorStatus.UNDEFINED,
                sensor=True,
                sensorid=None,
                camera=False,
                events=0,
                temperature=None,
                voltage=40,
            ),
            outputs=Outputs(output1=True, output2=False, output3=True),
            network=Network(ip=""),
            wifi=Wifi(SSID="", linkquality="", signal=""),
        )

    expected_attributes = {
        "device_class": "garage",
        "door_id": 1,
        "friendly_name": "mycontroller Door1",
        "is_closed": False,
        "supported_features": CoverEntityFeature.CLOSE | CoverEntityFeature.OPEN,
    }

    api = MagicMock(GogoGate2Api)
    api.async_activate.return_value = GogoGate2ActivateResponse(result=True)
    api.async_info.return_value = info_response(DoorStatus.OPENED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.OPENED,
        2: DoorStatus.OPENED,
    }
    gogogate2api_mock.return_value = api

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        title="mycontroller",
        data={
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )
    config_entry.add_to_hass(hass)

    assert hass.states.get("cover.mycontroller_door1") is None
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1").state == CoverState.OPEN
    assert (
        dict(hass.states.get("cover.mycontroller_door1").attributes)
        == expected_attributes
    )

    api.async_info.return_value = info_response(DoorStatus.CLOSED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.CLOSED,
        2: DoorStatus.CLOSED,
    }
    await hass.services.async_call(
        COVER_DOMAIN,
        "close_cover",
        service_data={"entity_id": "cover.mycontroller_door1"},
    )
    api.async_get_door_statuses_from_info.return_value = {
        1: TransitionDoorStatus.CLOSING,
        2: TransitionDoorStatus.CLOSING,
    }
    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1").state == CoverState.CLOSING
    api.async_close_door.assert_called_with(1)

    async_fire_time_changed(hass, utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1").state == CoverState.CLOSING

    api.async_info.return_value = info_response(DoorStatus.CLOSED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.CLOSED,
        2: DoorStatus.CLOSED,
    }
    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1").state == CoverState.CLOSED

    api.async_info.return_value = info_response(DoorStatus.OPENED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.OPENED,
        2: DoorStatus.OPENED,
    }
    await hass.services.async_call(
        COVER_DOMAIN,
        "open_cover",
        service_data={"entity_id": "cover.mycontroller_door1"},
    )
    api.async_get_door_statuses_from_info.return_value = {
        1: TransitionDoorStatus.OPENING,
        2: TransitionDoorStatus.OPENING,
    }
    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1").state == CoverState.OPENING
    api.async_open_door.assert_called_with(1)

    async_fire_time_changed(hass, utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1").state == CoverState.OPENING

    api.async_info.return_value = info_response(DoorStatus.OPENED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.OPENED,
        2: DoorStatus.OPENED,
    }
    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1").state == CoverState.OPEN

    api.async_info.return_value = info_response(DoorStatus.UNDEFINED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.UNDEFINED,
        2: DoorStatus.UNDEFINED,
    }
    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1").state == STATE_UNKNOWN

    api.async_info.return_value = info_response(DoorStatus.OPENED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.OPENED,
        2: DoorStatus.OPENED,
    }
    await hass.services.async_call(
        COVER_DOMAIN,
        "close_cover",
        service_data={"entity_id": "cover.mycontroller_door1"},
    )
    await hass.services.async_call(
        COVER_DOMAIN,
        "open_cover",
        service_data={"entity_id": "cover.mycontroller_door1"},
    )
    api.async_get_door_statuses_from_info.return_value = {
        1: TransitionDoorStatus.OPENING,
        2: TransitionDoorStatus.OPENING,
    }
    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1").state == CoverState.OPENING
    api.async_open_door.assert_called_with(1)

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert not hass.states.async_entity_ids(DOMAIN)