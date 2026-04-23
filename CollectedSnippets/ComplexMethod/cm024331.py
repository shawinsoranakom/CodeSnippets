async def test_set_asyncio_debug(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test setting asyncio debug."""

    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, SERVICE_SET_ASYNCIO_DEBUG)

    hass.loop.set_debug(False)
    original_level = logging.getLogger().getEffectiveLevel()
    logging.getLogger().setLevel(logging.WARNING)

    await hass.services.async_call(
        DOMAIN, SERVICE_SET_ASYNCIO_DEBUG, {CONF_ENABLED: False}, blocking=True
    )
    # Ensure logging level is only increased if we enable
    assert logging.getLogger().getEffectiveLevel() == logging.WARNING

    await hass.services.async_call(DOMAIN, SERVICE_SET_ASYNCIO_DEBUG, {}, blocking=True)
    assert hass.loop.get_debug() is True

    # Ensure logging is at least at INFO level
    assert logging.getLogger().getEffectiveLevel() == logging.INFO

    await hass.services.async_call(
        DOMAIN, SERVICE_SET_ASYNCIO_DEBUG, {CONF_ENABLED: False}, blocking=True
    )
    assert hass.loop.get_debug() is False

    await hass.services.async_call(
        DOMAIN, SERVICE_SET_ASYNCIO_DEBUG, {CONF_ENABLED: True}, blocking=True
    )
    assert hass.loop.get_debug() is True

    logging.getLogger().setLevel(original_level)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()