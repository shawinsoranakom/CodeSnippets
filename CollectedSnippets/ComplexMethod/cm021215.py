async def test_subentry_flow_reconfigure_plane_not_loaded(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfiguring a plane via subentry flow when entry is not loaded."""
    mock_config_entry.add_to_hass(hass)
    # Entry is not loaded, so it has no update listeners

    # Get the existing plane subentry id
    subentry_id = mock_config_entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE)[
        0
    ].subentry_id

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, SUBENTRY_TYPE_PLANE),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry_id},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_DECLINATION: 50,
            CONF_AZIMUTH: 200,
            CONF_MODULES_POWER: 6000,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    plane_subentries = mock_config_entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE)
    assert len(plane_subentries) == 1
    subentry = plane_subentries[0]
    assert subentry.data == {
        CONF_DECLINATION: 50,
        CONF_AZIMUTH: 200,
        CONF_MODULES_POWER: 6000,
    }
    assert subentry.title == "50° / 200° / 6000W"