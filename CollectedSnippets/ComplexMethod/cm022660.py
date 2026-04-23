async def test_activity_remote_bad_names(
    hass: HomeAssistant,
    hk_driver,
    events: list[Event],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test if remote accessory with invalid names works as expected."""
    entity_id = "remote.harmony"
    hass.states.async_set(
        entity_id,
        None,
        {
            ATTR_SUPPORTED_FEATURES: RemoteEntityFeature.ACTIVITY,
            ATTR_CURRENT_ACTIVITY: "Apple TV",
            ATTR_ACTIVITY_LIST: ["TV", "Apple TV", "[[[--Special--]]]", "Super"],
        },
    )
    await hass.async_block_till_done()
    acc = ActivityRemote(hass, hk_driver, "ActivityRemote", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 31  # Television

    assert acc.char_active.value == 0
    assert acc.char_remote_key.value == 0
    assert acc.char_input_source.value == 1

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: RemoteEntityFeature.ACTIVITY,
            ATTR_CURRENT_ACTIVITY: "[[[--Special--]]]",
            ATTR_ACTIVITY_LIST: ["TV", "Apple TV", "[[[--Special--]]]", "Super"],
        },
    )
    await hass.async_block_till_done()
    assert acc.char_active.value == 1
    assert acc.char_input_source.value == 2