async def test_number_action(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    service_data: dict[str, Any],
    expected_min: int,
    expected_target: int,
) -> None:
    """Test that service invokes renault_api with correct data for min charge limit."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    min_charge_level = hass.states.get("number.reg_zoe_40_minimum_charge_level")
    target_charge_level = hass.states.get("number.reg_zoe_40_target_charge_level")
    assert min_charge_level.state == "15"
    assert target_charge_level.state == "80"
    assert not min_charge_level.attributes.get(ATTR_ASSUMED_STATE)
    assert not target_charge_level.attributes.get(ATTR_ASSUMED_STATE)

    with patch(
        "renault_api.renault_vehicle.RenaultVehicle.set_battery_soc",
        return_value=(
            schemas.KamereonVehicleBatterySocActionDataSchema.loads(
                await async_load_fixture(hass, "action.set_battery_soc.json", DOMAIN)
            )
        ),
    ) as mock_action:
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            service_data=service_data,
            blocking=True,
        )
    assert len(mock_action.mock_calls) == 1
    mock_action.assert_awaited_once_with(min=expected_min, target=expected_target)

    # Verify optimistic update of coordinator data
    min_charge_level = hass.states.get("number.reg_zoe_40_minimum_charge_level")
    target_charge_level = hass.states.get("number.reg_zoe_40_target_charge_level")
    assert min_charge_level.state == str(expected_min)
    assert target_charge_level.state == str(expected_target)
    assert min_charge_level.attributes.get(ATTR_ASSUMED_STATE)
    assert target_charge_level.attributes.get(ATTR_ASSUMED_STATE)