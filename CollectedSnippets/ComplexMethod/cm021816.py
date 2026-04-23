async def test_buttons_pdu_dynamic_outlets(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    model: str,
    unique_id_base: str,
) -> None:
    """Tests that the button entities are correct."""

    list_commands_return_value = {
        supported_command: supported_command
        for supported_command in INTEGRATION_SUPPORTED_COMMANDS
    }

    for num in range(1, 25):
        command = f"outlet.{num!s}.load.cycle"
        list_commands_return_value[command] = command

    await async_init_integration(
        hass,
        model,
        list_commands_return_value=list_commands_return_value,
    )

    entity_id = "button.ups1_power_cycle_outlet_a1"
    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == f"{unique_id_base}outlet.1.load.cycle"

    button = hass.states.get(entity_id)
    assert button
    assert button.state == STATE_UNKNOWN

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    button = hass.states.get(entity_id)
    assert button.state != STATE_UNKNOWN

    button = hass.states.get("button.ups1_power_cycle_outlet_25")
    assert not button

    button = hass.states.get("button.ups1_power_cycle_outlet_a25")
    assert not button