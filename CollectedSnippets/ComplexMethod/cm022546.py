async def test_if_fires_on_hass_start(
    hass: HomeAssistant, hass_config: ConfigType
) -> None:
    """Test the firing when Home Assistant starts."""
    calls = async_mock_service(hass, "test", "automation")
    hass.set_state(CoreState.not_running)

    assert await async_setup_component(hass, automation.DOMAIN, hass_config)
    assert automation.is_on(hass, "automation.hello")
    assert len(calls) == 0

    await hass.async_start()
    await hass.async_block_till_done()
    assert automation.is_on(hass, "automation.hello")
    assert len(calls) == 1

    await hass.services.async_call(
        automation.DOMAIN, automation.SERVICE_RELOAD, blocking=True
    )

    assert automation.is_on(hass, "automation.hello")
    assert len(calls) == 1
    assert calls[0].data["id"] == 0