async def test_zeroconf_flow_success(hass: HomeAssistant) -> None:
    """Test the zeroconf discovery flow with successful configuration."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=DISCOVERY_INFO
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"

    # Display the confirmation form
    result = await hass.config_entries.flow.async_configure(result["flow_id"], None)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"

    # Proceed to creating the entry
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_HOSTNAME
    assert result["data"][CONF_HOST] == TEST_HOSTNAME
    assert result["data"][CONF_MAC] == TEST_SIMPLE_MAC
    assert result["result"].unique_id == TEST_SIMPLE_MAC