async def test_reauth_flow_update_configuration_on_not_loaded_entry(
    hass: HomeAssistant, config_entry_factory: ConfigEntryFactoryType
) -> None:
    """Verify reauth flow can update hub configuration on a not loaded entry."""
    with patch(
        "homeassistant.components.unifi.get_unifi_api",
        side_effect=CannotConnect,
    ):
        config_entry = await config_entry_factory()

    result = await config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "1.2.3.4",
            CONF_USERNAME: "new_name",
            CONF_PASSWORD: "new_pass",
            CONF_PORT: 1234,
            CONF_VERIFY_SSL: True,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[CONF_HOST] == "1.2.3.4"
    assert config_entry.data[CONF_USERNAME] == "new_name"
    assert config_entry.data[CONF_PASSWORD] == "new_pass"