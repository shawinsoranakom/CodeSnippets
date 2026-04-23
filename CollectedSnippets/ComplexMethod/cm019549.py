async def test_train(hass: HomeAssistant) -> None:
    """Test for operational uk_transport sensor with proper attributes."""
    with (
        requests_mock.Mocker() as mock_req,
        patch("homeassistant.util.dt.now", return_value=now().replace(hour=13)),
    ):
        uri = re.compile(UkTransportSensor.TRANSPORT_API_URL_BASE + "*")
        mock_req.get(
            uri, text=await async_load_fixture(hass, "uk_transport/train.json")
        )
        assert await async_setup_component(hass, "sensor", VALID_CONFIG)
        await hass.async_block_till_done()

    train_state = hass.states.get("sensor.next_train_to_WAT")
    assert None is not train_state
    assert train_state.name == f"Next train to {TRAIN_DESTINATION_NAME}"
    assert train_state.attributes[ATTR_STATION_CODE] == TRAIN_STATION_CODE
    assert train_state.attributes[ATTR_CALLING_AT] == TRAIN_DESTINATION_NAME
    assert len(train_state.attributes.get(ATTR_NEXT_TRAINS)) == 25

    assert (
        train_state.attributes[ATTR_NEXT_TRAINS][0]["destination_name"]
        == "London Waterloo"
    )
    assert train_state.attributes[ATTR_NEXT_TRAINS][0]["estimated"] == "06:13"
    assert train_state.attributes[ATTR_LAST_UPDATED] == "2017-07-10T06:10:05+01:00"