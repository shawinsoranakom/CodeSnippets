async def test_services(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test Flo services."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert aioclient_mock.call_count == 8

    await hass.services.async_call(
        DOMAIN,
        SERVICE_RUN_HEALTH_TEST,
        {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 9

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_AWAY_MODE,
        {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 10

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_HOME_MODE,
        {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 11

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_SLEEP_MODE,
        {
            ATTR_ENTITY_ID: SWITCH_ENTITY_ID,
            ATTR_REVERT_TO_MODE: SYSTEM_MODE_HOME,
            ATTR_SLEEP_MINUTES: 120,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 12

    # test calling with a string value to ensure it is converted to int
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_SLEEP_MODE,
        {
            ATTR_ENTITY_ID: SWITCH_ENTITY_ID,
            ATTR_REVERT_TO_MODE: SYSTEM_MODE_HOME,
            ATTR_SLEEP_MINUTES: "120",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 13

    # test calling with a non string -> int value and ensure exception is thrown
    with pytest.raises(MultipleInvalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_SLEEP_MODE,
            {
                ATTR_ENTITY_ID: SWITCH_ENTITY_ID,
                ATTR_REVERT_TO_MODE: SYSTEM_MODE_HOME,
                ATTR_SLEEP_MINUTES: "test",
            },
            blocking=True,
        )
    assert aioclient_mock.call_count == 13