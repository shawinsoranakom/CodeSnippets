async def test_application_state(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    mock_device: RokuDevice,
    mock_roku: MagicMock,
) -> None:
    """Test the creation and values of the Roku selects."""
    entity_registry.async_get_or_create(
        SELECT_DOMAIN,
        DOMAIN,
        "1GU48T017973_application",
        suggested_object_id="my_roku_3_application",
        disabled_by=None,
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("select.my_roku_3_application")
    assert state
    assert state.attributes.get(ATTR_OPTIONS) == [
        "Home",
        "Amazon Video on Demand",
        "Free FrameChannel Service",
        "MLB.TV" + "\u00ae",
        "Mediafly",
        "Netflix",
        "Pandora",
        "Pluto TV - It's Free TV",
        "Roku Channel Store",
    ]
    assert state.state == "Home"

    entry = entity_registry.async_get("select.my_roku_3_application")
    assert entry
    assert entry.unique_id == "1GU48T017973_application"

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.my_roku_3_application",
            ATTR_OPTION: "Netflix",
        },
        blocking=True,
    )

    assert mock_roku.launch.call_count == 1
    mock_roku.launch.assert_called_with("12")
    mock_device.app = mock_device.apps[1]

    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()

    state = hass.states.get("select.my_roku_3_application")
    assert state

    assert state.state == "Netflix"

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.my_roku_3_application",
            ATTR_OPTION: "Home",
        },
        blocking=True,
    )

    assert mock_roku.remote.call_count == 1
    mock_roku.remote.assert_called_with("home")
    mock_device.app = Application(
        app_id=None, name="Roku", version=None, screensaver=None
    )
    async_fire_time_changed(hass, dt_util.utcnow() + (SCAN_INTERVAL * 2))
    await hass.async_block_till_done()

    state = hass.states.get("select.my_roku_3_application")
    assert state
    assert state.state == "Home"