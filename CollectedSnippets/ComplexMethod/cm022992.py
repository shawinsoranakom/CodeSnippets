async def test_user_flow_success(hass: HomeAssistant) -> None:
    """Test the user flow with successful configuration."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: TEST_IP}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_IP
    assert result["data"][CONF_MAC] == TEST_SIMPLE_MAC
    assert result["data"][CONF_IP_ADDRESS] == TEST_IP
    assert result["data"][CONF_DEVICE] is not None
    assert result["data"][CONF_WEBHOOK_ID] is not None

    # Since this is user flow, there is no hostname, so hostname should be the IP address
    assert result["data"][CONF_HOST] == TEST_IP
    assert result["result"].unique_id == TEST_SIMPLE_MAC

    # Confirm that the entry was created
    entries = hass.config_entries.async_entries(domain=DOMAIN)
    assert len(entries) == 1