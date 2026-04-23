async def test_minio_listen(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture, minio_client_event
) -> None:
    """Test minio listen on notifications."""
    minio_client_event.presigned_get_object.return_value = "http://url"

    events = []

    @callback
    def event_callback(event):
        """Handle event callbback."""
        events.append(event)

    hass.bus.async_listen("minio", event_callback)

    await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                CONF_HOST: "localhost",
                CONF_PORT: "9000",
                CONF_ACCESS_KEY: "abcdef",
                CONF_SECRET_KEY: "0123456789",
                CONF_SECURE: "true",
                CONF_LISTEN: [{CONF_LISTEN_BUCKET: "test"}],
            }
        },
    )

    await hass.async_start()
    await hass.async_block_till_done()

    while not events:
        await asyncio.sleep(0)

    assert len(events) == 1
    event = events[0]

    assert event.event_type == DOMAIN
    assert event.data["event_name"] == "s3:ObjectCreated:Put"
    assert event.data["file_name"] == "5jJkTAo.jpg"
    assert event.data["bucket"] == "test"
    assert event.data["key"] == "5jJkTAo.jpg"
    assert event.data["presigned_url"] == "http://url"
    assert len(event.data["metadata"]) == 0