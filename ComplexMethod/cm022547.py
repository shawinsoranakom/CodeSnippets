async def test_if_fires_on_hass_shutdown(hass: HomeAssistant) -> None:
    """Test the firing when Home Assistant shuts down."""
    calls = async_mock_service(hass, "test", "automation")
    hass.set_state(CoreState.not_running)

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "homeassistant", "event": "shutdown"},
                "action": {
                    "service": "test.automation",
                    "data_template": {"id": "{{ trigger.id}}"},
                },
            }
        },
    )
    assert automation.is_on(hass, "automation.hello")
    assert len(calls) == 0

    await hass.async_start()
    assert automation.is_on(hass, "automation.hello")
    await hass.async_block_till_done()
    assert len(calls) == 0

    with patch.object(hass.loop, "stop"):
        await hass.async_stop()
    assert len(calls) == 1
    assert calls[0].data["id"] == 0