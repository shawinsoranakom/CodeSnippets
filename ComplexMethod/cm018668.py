async def test_map_status_change(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    hass_client: ClientSessionGenerator,
    fake_vacuum: FakeDevice,
) -> None:
    """Test floor plan map image is correctly updated on status change."""
    assert len(hass.states.async_all("image")) == 4

    assert hass.states.get("image.roborock_s7_maxv_upstairs") is not None
    client = await hass_client()
    resp = await client.get("/api/image_proxy/image.roborock_s7_maxv_upstairs")
    assert resp.status == HTTPStatus.OK
    old_body = await resp.read()
    assert old_body == b"\x89PNG-001"

    _LOGGER.debug("First image fetch complete")

    # Call a second time. This interval does not directly trigger a map update, but does
    # trigger a status update which detects the state has changed and uddates the map
    now = dt_util.utcnow() + V1_LOCAL_NOT_CLEANING_INTERVAL

    assert fake_vacuum.v1_properties
    fake_vacuum.v1_properties.status.state = RoborockStateCode.returning_home
    fake_vacuum.v1_properties.home.home_map_content = {
        0: MapContent(
            image_content=b"\x89PNG-003",
            map_data=copy.deepcopy(MAP_DATA),
        )
    }

    with patch(
        "homeassistant.components.roborock.coordinator.dt_util.utcnow",
        return_value=now,
    ):
        async_fire_time_changed(hass, now)
        # Refresh device in the background
        await hass.async_block_till_done()

        resp = await client.get("/api/image_proxy/image.roborock_s7_maxv_upstairs")

        assert resp.status == HTTPStatus.OK
        body = await resp.read()
        assert body is not None
        assert body != old_body