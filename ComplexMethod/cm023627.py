async def test_openalpr_process_image(
    alpr_events,
    setup_openalpr_cloud,
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Set up and scan a picture and test plates from event."""
    aioclient_mock.post(
        OPENALPR_API_URL,
        params=PARAMS,
        text=await async_load_fixture(hass, "alpr_cloud.json", "openalpr_cloud"),
        status=200,
    )

    with patch(
        "homeassistant.components.camera.async_get_image",
        return_value=camera.Image("image/jpeg", b"image"),
    ):
        common.async_scan(hass, entity_id="image_processing.test_local")
        await hass.async_block_till_done()

    state = hass.states.get("image_processing.test_local")

    assert len(aioclient_mock.mock_calls) == 1
    assert len(alpr_events) == 5
    assert state.attributes.get("vehicles") == 1
    assert state.state == "H786P0J"

    event_data = [
        event.data for event in alpr_events if event.data.get("plate") == "H786P0J"
    ]
    assert len(event_data) == 1
    assert event_data[0]["plate"] == "H786P0J"
    assert event_data[0]["confidence"] == 90.436699
    assert event_data[0]["entity_id"] == "image_processing.test_local"