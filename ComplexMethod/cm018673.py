async def test_q7_state_changing_commands(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    service: str,
    api_method: str,
    service_params: dict[str, Any] | None,
    expected_activity: str,
    q7_vacuum_api: Mock,
    fake_q7_vacuum: FakeDevice,
) -> None:
    """Test sending state-changing commands to the Q7 vacuum."""
    vacuum = hass.states.get(Q7_ENTITY_ID)
    assert vacuum

    data = {ATTR_ENTITY_ID: Q7_ENTITY_ID, **(service_params or {})}
    await hass.services.async_call(
        VACUUM_DOMAIN,
        service,
        data,
        blocking=True,
    )
    api_call = getattr(q7_vacuum_api, api_method)
    assert api_call.call_count == 1
    assert api_call.call_args[0] == ()

    # Verify the entity state was updated
    assert fake_q7_vacuum.b01_q7_properties is not None
    # Force coordinator refresh to get updated state
    coordinator = setup_entry.runtime_data.b01_q7[0]

    await coordinator.async_refresh()
    await hass.async_block_till_done()
    vacuum = hass.states.get(Q7_ENTITY_ID)
    assert vacuum
    assert vacuum.state == expected_activity