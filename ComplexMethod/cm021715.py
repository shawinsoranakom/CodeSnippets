async def test_zeroconf(
    hass: HomeAssistant,
    mock_kiosker_api: MagicMock,
) -> None:
    """Test the zeroconf discovery happy flow creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"
    assert result["description_placeholders"] == {
        "name": "python-test-device (A98BE1CE)",
        "host": "192.168.1.39",
    }
    schema_keys = list(result["data_schema"].schema.keys())
    assert any(key.schema == CONF_API_TOKEN for key in schema_keys)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_TOKEN: "test-token",
            CONF_VERIFY_SSL: False,
        },
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Kiosker A98BE1CE"
    assert result2["data"] == {
        CONF_HOST: "192.168.1.39",
        CONF_API_TOKEN: "test-token",
        CONF_SSL: True,
        CONF_VERIFY_SSL: False,
    }
    assert result2["result"].unique_id == "A98BE1CE-5FE7-4A8D-B2C3-123456789ABC"