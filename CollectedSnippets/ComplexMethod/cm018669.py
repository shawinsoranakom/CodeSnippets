async def test_q10_cleaning_mode_select_current_option(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    fake_q10_vacuum: FakeDevice,
) -> None:
    """Test Q10 cleaning mode select entity current option."""
    entity_id = "select.roborock_q10_s5_cleaning_mode"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNKNOWN
    options = state.attributes.get("options")
    assert options is not None
    assert set(options) == {"vac_and_mop", "vacuum", "mop"}

    assert fake_q10_vacuum.b01_q10_properties
    fake_q10_vacuum.b01_q10_properties.status.update_from_dps(
        {B01_Q10_DP.CLEAN_MODE: YXCleanType.VAC_AND_MOP.code}
    )
    await hass.async_block_till_done()

    updated_state = hass.states.get(entity_id)
    assert updated_state is not None
    assert updated_state.state == "vac_and_mop"