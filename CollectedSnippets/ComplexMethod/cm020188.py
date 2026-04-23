async def test_triggers(
    hass: HomeAssistant, tag_setup, service_calls: list[ServiceCall]
) -> None:
    """Test tag triggers."""
    assert await tag_setup()
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "alias": "test",
                    "trigger": {"platform": DOMAIN, TAG_ID: "abc123"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "message": "service called",
                            "id": "{{ trigger.id}}",
                        },
                    },
                }
            ]
        },
    )

    await hass.async_block_till_done()

    await async_scan_tag(hass, "abc123", None)
    await hass.async_block_till_done()

    assert len(service_calls) == 1
    assert service_calls[0].data["message"] == "service called"
    assert service_calls[0].data["id"] == 0

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "automation.test"},
        blocking=True,
    )
    assert len(service_calls) == 2

    await async_scan_tag(hass, "abc123", None)
    await hass.async_block_till_done()

    assert len(service_calls) == 2