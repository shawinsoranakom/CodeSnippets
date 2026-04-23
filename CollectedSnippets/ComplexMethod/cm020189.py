async def test_multiple_tags_and_devices_trigger(
    hass: HomeAssistant, tag_setup, service_calls: list[ServiceCall]
) -> None:
    """Test multiple tags and devices triggers."""
    assert await tag_setup()
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": DOMAIN,
                        TAG_ID: ["abc123", "def456"],
                        DEVICE_ID: ["ghi789", "jkl0123"],
                    },
                    "action": {
                        "service": "test.automation",
                        "data": {"message": "service called"},
                    },
                }
            ]
        },
    )

    await hass.async_block_till_done()

    # Should not trigger
    await async_scan_tag(hass, tag_id="abc123", device_id=None)
    await async_scan_tag(hass, tag_id="abc123", device_id="invalid")
    await hass.async_block_till_done()

    # Should trigger
    await async_scan_tag(hass, tag_id="abc123", device_id="ghi789")
    await hass.async_block_till_done()
    await async_scan_tag(hass, tag_id="abc123", device_id="jkl0123")
    await hass.async_block_till_done()
    await async_scan_tag(hass, "def456", device_id="ghi789")
    await hass.async_block_till_done()
    await async_scan_tag(hass, "def456", device_id="jkl0123")
    await hass.async_block_till_done()

    assert len(service_calls) == 4
    assert service_calls[0].data["message"] == "service called"
    assert service_calls[1].data["message"] == "service called"
    assert service_calls[2].data["message"] == "service called"
    assert service_calls[3].data["message"] == "service called"