async def test_q10_push_status_update(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    fake_q10_vacuum: FakeDevice,
) -> None:
    """Test that a push status update from the device updates entity state.

    Simulates the real flow: device pushes DPS data over MQTT,
    StatusTrait parses it via update_from_dps, notifies listeners,
    and the entity calls async_write_ha_state.
    """
    assert fake_q10_vacuum.b01_q10_properties is not None
    api = fake_q10_vacuum.b01_q10_properties

    # Verify initial state is "docked" (from Q10_STATUS fixture: CHARGING)
    vacuum = hass.states.get(Q10_ENTITY_ID)
    assert vacuum
    assert vacuum.state == "docked"

    # Simulate the device pushing a status change via DPS data
    # (e.g. user started cleaning from the Roborock app)
    api.status.update_from_dps({B01_Q10_DP.STATUS: 5})  # CLEANING
    await hass.async_block_till_done()

    # Verify the entity state updated to "cleaning"
    vacuum = hass.states.get(Q10_ENTITY_ID)
    assert vacuum
    assert vacuum.state == "cleaning"

    # Simulate returning to dock
    api.status.update_from_dps({B01_Q10_DP.STATUS: 6})  # RETURNING_HOME
    await hass.async_block_till_done()

    vacuum = hass.states.get(Q10_ENTITY_ID)
    assert vacuum
    assert vacuum.state == "returning"