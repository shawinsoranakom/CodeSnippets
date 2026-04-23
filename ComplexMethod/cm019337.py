async def test_zero_conf_second_envoy_while_form(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    mock_envoy: AsyncMock,
) -> None:
    """Test zeroconf while form is active."""
    await setup_integration(hass, config_entry)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("4.4.4.4"),
            ip_addresses=[ip_address("4.4.4.4")],
            hostname="mock_hostname",
            name="mock_name",
            port=None,
            properties={"serialnum": "4321", "protovers": "7.0.1"},
            type="mock_type",
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert config_entry.data[CONF_HOST] == "1.1.1.1"
    assert config_entry.unique_id == "1234"
    assert config_entry.title == "Envoy 1234"

    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_HOST: "4.4.4.4",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Envoy 4321"
    assert result2["result"].unique_id == "4321"

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    assert result4["type"] is FlowResultType.ABORT