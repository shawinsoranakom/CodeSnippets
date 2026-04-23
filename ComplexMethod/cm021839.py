async def test_config_already_registered_not_passed_to_config_entry(
    hass: HomeAssistant, simple_mock_home
) -> None:
    """Test that an already registered accesspoint does not get imported."""

    mock_config = {HMIPC_AUTHTOKEN: "123", HMIPC_HAPID: "ABC123", HMIPC_NAME: "name"}
    MockConfigEntry(domain=DOMAIN, data=mock_config).add_to_hass(hass)

    # one config_entry exists
    config_entries = hass.config_entries.async_entries(DOMAIN)
    assert len(config_entries) == 1
    assert config_entries[0].data == {
        "authtoken": "123",
        "hapid": "ABC123",
        "name": "name",
    }
    # config_enty has no unique_id
    assert not config_entries[0].unique_id

    entry_config = {
        CONF_ACCESSPOINT: "ABC123",
        CONF_AUTHTOKEN: "123",
        CONF_NAME: "name",
    }

    with patch(
        "homeassistant.components.homematicip_cloud.hap.HomematicipHAP.async_connect",
    ):
        assert await async_setup_component(hass, DOMAIN, {DOMAIN: entry_config})

    # no new config_entry created / still one config_entry
    config_entries = hass.config_entries.async_entries(DOMAIN)
    assert len(config_entries) == 1
    assert config_entries[0].data == {
        "authtoken": "123",
        "hapid": "ABC123",
        "name": "name",
    }
    # config_enty updated with unique_id
    assert config_entries[0].unique_id == "ABC123"