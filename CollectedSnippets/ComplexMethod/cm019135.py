async def test_start_selected_program(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
    additional_service_data: dict[str, Any],
    options_already_set: list[Option] | None,
    get_active_program_side_effect: NoProgramActiveError | None,
    get_selected_program_call_count: int,
    snapshot: SnapshotAssertion,
) -> None:
    """Test starting the selected program with optional parameter overrides."""
    client.get_active_program = AsyncMock(
        return_value=Program(
            key=ProgramKey.DISHCARE_DISHWASHER_ECO_50,
            options=options_already_set,
        ),
        side_effect=get_active_program_side_effect,
    )
    client.get_selected_program = AsyncMock(
        return_value=Program(
            key=ProgramKey.DISHCARE_DISHWASHER_ECO_50,
            options=options_already_set,
        )
    )

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, appliance.ha_id)},
    )

    await hass.services.async_call(
        domain=DOMAIN,
        service="start_selected_program",
        service_data={
            "device_id": device_entry.id,
            **additional_service_data,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    client.get_active_program.assert_awaited_once_with(appliance.ha_id)
    assert client.get_selected_program.call_count == get_selected_program_call_count
    for call_args in client.start_program.call_args_list:
        assert call_args[0][0] == appliance.ha_id
    assert client.start_program.call_count == 1
    assert client.start_program.call_args == snapshot