async def test_unique_id_migrate(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test we can migrate unique ids of the sensors."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={CONF_IP_ADDRESS: "1.2.3.4"})
    config_entry.add_to_hass(hass)

    mock_powerwall = await _mock_powerwall_with_fixtures(hass)
    old_unique_id = "_".join(sorted(["TG0123456789AB", "TG9876543210BA"]))
    new_unique_id = MOCK_GATEWAY_DIN
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("powerwall", old_unique_id)},
        manufacturer="Tesla",
    )
    old_mysite_load_power_entity = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        unique_id=f"{old_unique_id}_load_instant_power",
        suggested_object_id="mysite_load_power",
        config_entry=config_entry,
    )
    assert old_mysite_load_power_entity.entity_id == "sensor.mysite_load_power"

    with (
        patch(
            "homeassistant.components.powerwall.config_flow.Powerwall",
            return_value=mock_powerwall,
        ),
        patch(
            "homeassistant.components.powerwall.Powerwall", return_value=mock_powerwall
        ),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    reg_device = device_registry.async_get_device(
        identifiers={("powerwall", MOCK_GATEWAY_DIN)},
    )
    old_reg_device = device_registry.async_get_device(
        identifiers={("powerwall", old_unique_id)},
    )
    assert old_reg_device is None
    assert reg_device is not None

    assert (
        entity_registry.async_get_entity_id(
            "sensor", DOMAIN, f"{old_unique_id}_load_instant_power"
        )
        is None
    )
    assert (
        entity_registry.async_get_entity_id(
            "sensor", DOMAIN, f"{new_unique_id}_load_instant_power"
        )
        is not None
    )

    state = hass.states.get("sensor.mysite_load_power")
    assert state.state == "1.971"