async def test_face_event_call(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Set up and scan a picture and test faces from event."""
    face_events = await setup_image_processing_face(hass)
    aioclient_mock.get(get_url(hass), content=b"image")

    common.async_scan(hass, entity_id="image_processing.demo_face")
    await hass.async_block_till_done()

    state = hass.states.get("image_processing.demo_face")

    assert len(face_events) == 2
    assert state.state == "Hans"
    assert state.attributes["total_faces"] == 4

    event_data = [
        event.data for event in face_events if event.data.get("name") == "Hans"
    ]
    assert len(event_data) == 1
    assert event_data[0]["name"] == "Hans"
    assert event_data[0]["confidence"] == 98.34
    assert event_data[0]["gender"] == "male"
    assert event_data[0]["entity_id"] == "image_processing.demo_face"