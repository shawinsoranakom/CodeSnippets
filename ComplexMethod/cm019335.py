async def test_zeroconf(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_envoy: AsyncMock,
    version: str,
    schema_username: str,
) -> None:
    """Test we can setup from zeroconf."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("1.1.1.1"),
            ip_addresses=[ip_address("1.1.1.1")],
            hostname="mock_hostname",
            name="mock_name",
            port=None,
            properties={"serialnum": "1234", "protovers": version},
            type="mock_type",
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert (
        _get_schema_default(result["data_schema"].schema, CONF_USERNAME)
        == schema_username
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Envoy 1234"
    assert result2["result"].unique_id == "1234"
    assert result2["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_NAME: "Envoy 1234",
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
    }