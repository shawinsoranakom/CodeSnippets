async def test_split_foundation_preset(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_asyncsleepiq: MagicMock,
) -> None:
    """Test the SleepIQ select entity for split foundation presets."""
    entry = await setup_platform(hass, SELECT_DOMAIN)

    state = hass.states.get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_foundation_preset_right"
    )
    assert state.state == PRESET_R_STATE
    assert state.attributes.get(ATTR_ICON) == "mdi:bed"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} Foundation Preset Right"
    )

    entry = entity_registry.async_get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_foundation_preset_right"
    )
    assert entry
    assert entry.unique_id == f"{BED_ID}_preset_R"

    state = hass.states.get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_foundation_preset_left"
    )
    assert state.state == PRESET_L_STATE
    assert state.attributes.get(ATTR_ICON) == "mdi:bed"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} Foundation Preset Left"
    )

    entry = entity_registry.async_get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_foundation_preset_left"
    )
    assert entry
    assert entry.unique_id == f"{BED_ID}_preset_L"

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_foundation_preset_left",
            ATTR_OPTION: "Zero G",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_asyncsleepiq.beds[BED_ID].foundation.presets[0].set_preset.assert_called_once()
    mock_asyncsleepiq.beds[BED_ID].foundation.presets[0].set_preset.assert_called_with(
        "Zero G"
    )