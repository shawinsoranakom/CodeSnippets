async def test_see_service(mock_see, hass: HomeAssistant) -> None:
    """Test the see service with a unicode dev_id and NO MAC."""
    with assert_setup_component(1, device_tracker.DOMAIN):
        assert await async_setup_component(hass, device_tracker.DOMAIN, TEST_PLATFORM)
        await hass.async_block_till_done()
    params = {
        "dev_id": "some_device",
        "host_name": "example.com",
        "location_name": "Work",
        "gps": [0.3, 0.8],
        "attributes": {"test": "test"},
    }
    common.async_see(hass, **params)
    await hass.async_block_till_done()
    assert mock_see.call_count == 1
    assert mock_see.call_count == 1
    assert mock_see.call_args == call(**params)

    mock_see.reset_mock()
    params["dev_id"] += chr(233)  # e' acute accent from icloud

    common.async_see(hass, **params)
    await hass.async_block_till_done()
    assert mock_see.call_count == 1
    assert mock_see.call_count == 1
    assert mock_see.call_args == call(**params)