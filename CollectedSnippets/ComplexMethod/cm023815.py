async def test_async_setup_entry_sets_up_hub_and_supported_domains(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test that configuring entry sets up cover domain."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )

    with (
        patch_bond_bridge(),
        patch_bond_version(
            return_value={
                "bondid": "ZXXX12345",
                "target": "test-model",
                "fw_ver": "test-version",
                "mcu_ver": "test-hw-version",
            }
        ),
        patch_setup_entry("cover") as mock_cover_async_setup_entry,
        patch_setup_entry("fan") as mock_fan_async_setup_entry,
        patch_setup_entry("light") as mock_light_async_setup_entry,
        patch_setup_entry("switch") as mock_switch_async_setup_entry,
    ):
        result = await setup_bond_entity(hass, config_entry, patch_device_ids=True)
        assert result is True
        await hass.async_block_till_done()

    assert isinstance(config_entry.runtime_data, BondData)
    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.unique_id == "ZXXX12345"

    # verify hub device is registered correctly
    hub = device_registry.async_get_device(identifiers={(DOMAIN, "ZXXX12345")})
    assert hub.name == "bond-name"
    assert hub.manufacturer == "Olibra"
    assert hub.model == "test-model"
    assert hub.sw_version == "test-version"
    assert hub.hw_version == "test-hw-version"
    assert hub.configuration_url == "http://some host"

    # verify supported domains are setup
    assert len(mock_cover_async_setup_entry.mock_calls) == 1
    assert len(mock_fan_async_setup_entry.mock_calls) == 1
    assert len(mock_light_async_setup_entry.mock_calls) == 1
    assert len(mock_switch_async_setup_entry.mock_calls) == 1