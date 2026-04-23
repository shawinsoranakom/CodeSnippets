async def test_ms_identify_process_image(
    hass: HomeAssistant, poll_mock, aioclient_mock: AiohttpClientMocker
) -> None:
    """Set up and scan a picture and test plates from event."""
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups"),
        text=await async_load_fixture(
            hass, "persongroups.json", "microsoft_face_identify"
        ),
    )
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups/test_group1/persons"),
        text=await async_load_fixture(hass, "persons.json", "microsoft_face_identify"),
    )
    aioclient_mock.get(
        ENDPOINT_URL.format("persongroups/test_group2/persons"),
        text=await async_load_fixture(hass, "persons.json", "microsoft_face_identify"),
    )

    await async_setup_component(hass, IP_DOMAIN, CONFIG)
    await hass.async_block_till_done()

    state = hass.states.get("camera.demo_camera")
    url = f"{hass.config.internal_url}{state.attributes.get(ATTR_ENTITY_PICTURE)}"

    face_events = []

    @callback
    def mock_face_event(event):
        """Mock event."""
        face_events.append(event)

    hass.bus.async_listen("image_processing.detect_face", mock_face_event)

    aioclient_mock.get(url, content=b"image")

    aioclient_mock.post(
        ENDPOINT_URL.format("detect"),
        text=await async_load_fixture(hass, "detect.json", "microsoft_face_identify"),
    )
    aioclient_mock.post(
        ENDPOINT_URL.format("identify"),
        text=await async_load_fixture(hass, "identify.json", "microsoft_face_identify"),
    )

    common.async_scan(hass, entity_id="image_processing.test_local")
    await hass.async_block_till_done()

    state = hass.states.get("image_processing.test_local")

    assert len(face_events) == 1
    assert state.attributes.get("total_faces") == 2
    assert state.state == "David"

    assert face_events[0].data["name"] == "David"
    assert face_events[0].data["confidence"] == float(92)
    assert face_events[0].data["entity_id"] == "image_processing.test_local"

    # Test that later, if a request is made that results in no face
    # being detected, that this is reflected in the state object
    aioclient_mock.clear_requests()
    aioclient_mock.post(ENDPOINT_URL.format("detect"), text="[]")

    common.async_scan(hass, entity_id="image_processing.test_local")
    await hass.async_block_till_done()

    state = hass.states.get("image_processing.test_local")

    # No more face events were fired
    assert len(face_events) == 1
    # Total faces and actual qualified number of faces reset to zero
    assert state.attributes.get("total_faces") == 0
    assert state.state == STATE_UNKNOWN