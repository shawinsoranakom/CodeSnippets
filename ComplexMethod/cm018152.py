async def test_operation_mode_validation(
    hass: HomeAssistant, config_flow_fixture: None
) -> None:
    """Test operation mode validation."""
    water_heater_entity = MockWaterHeaterEntity()
    water_heater_entity.hass = hass
    water_heater_entity._attr_name = "test"
    water_heater_entity._attr_unique_id = "test"
    water_heater_entity._attr_supported_features = (
        WaterHeaterEntityFeature.OPERATION_MODE
    )
    water_heater_entity._attr_current_operation = None
    water_heater_entity._attr_operation_list = None

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.WATER_HEATER]
        )
        return True

    async def async_setup_entry_water_heater_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test water_heater platform via config entry."""
        async_add_entities([water_heater_entity])

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=async_setup_entry_init,
        ),
        built_in=False,
    )
    mock_platform(
        hass,
        "test.water_heater",
        MockPlatform(async_setup_entry=async_setup_entry_water_heater_platform),
    )

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)

    data = {"entity_id": "water_heater.test", "operation_mode": "test"}

    with pytest.raises(ServiceValidationError) as exc:
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_OPERATION_MODE, data, blocking=True
        )
    assert (
        str(exc.value) == "Operation mode test is not valid for water_heater.test. "
        "The operation list is not defined"
    )
    assert exc.value.translation_domain == DOMAIN
    assert exc.value.translation_key == "operation_list_not_defined"
    assert exc.value.translation_placeholders == {
        "entity_id": "water_heater.test",
        "operation_mode": "test",
    }

    water_heater_entity._attr_operation_list = ["gas", "eco"]
    with pytest.raises(ServiceValidationError) as exc:
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_OPERATION_MODE, data, blocking=True
        )
    assert (
        str(exc.value) == "Operation mode test is not valid for water_heater.test. "
        "Valid operation modes are: gas, eco"
    )
    assert exc.value.translation_domain == DOMAIN
    assert exc.value.translation_key == "not_valid_operation_mode"
    assert exc.value.translation_placeholders == {
        "entity_id": "water_heater.test",
        "operation_mode": "test",
        "operation_list": "gas, eco",
    }

    data = {"entity_id": "water_heater.test", "operation_mode": "eco"}
    await hass.services.async_call(
        DOMAIN, SERVICE_SET_OPERATION_MODE, data, blocking=True
    )
    await hass.async_block_till_done()
    water_heater_entity.set_operation_mode.assert_has_calls([mock.call("eco")])