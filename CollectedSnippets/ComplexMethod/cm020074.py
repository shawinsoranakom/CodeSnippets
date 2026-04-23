async def test_init_connection_handling(
    hass: HomeAssistant,
    knx: KNXTestKit,
    config_entry_data: KNXConfigEntryData,
    connection_config: ConnectionConfig,
) -> None:
    """Test correctly generating connection config."""

    config_entry = MockConfigEntry(
        title="KNX",
        domain=DOMAIN,
        data=config_entry_data,
    )
    knx.mock_config_entry = config_entry
    await knx.setup_integration()

    assert hass.data.get(DOMAIN) is not None

    original_connection_config = hass.data[DOMAIN].connection_config().__dict__.copy()
    del original_connection_config["secure_config"]

    connection_config_dict = connection_config.__dict__.copy()
    del connection_config_dict["secure_config"]

    assert original_connection_config == connection_config_dict

    if connection_config.secure_config is not None:
        assert (
            hass.data[DOMAIN].connection_config().secure_config.knxkeys_password
            == connection_config.secure_config.knxkeys_password
        )
        assert (
            hass.data[DOMAIN].connection_config().secure_config.user_password
            == connection_config.secure_config.user_password
        )
        assert (
            hass.data[DOMAIN].connection_config().secure_config.user_id
            == connection_config.secure_config.user_id
        )
        assert (
            hass.data[DOMAIN]
            .connection_config()
            .secure_config.device_authentication_password
            == connection_config.secure_config.device_authentication_password
        )
        if connection_config.secure_config.knxkeys_file_path is not None:
            assert (
                connection_config.secure_config.knxkeys_file_path
                in hass.data[DOMAIN].connection_config().secure_config.knxkeys_file_path
            )