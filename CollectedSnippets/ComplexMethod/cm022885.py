async def test_form_dhcp_with_polisy(hass: HomeAssistant) -> None:
    """Test we can setup from dhcp with polisy."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.2.3.4",
            hostname="polisy",
            macaddress=MOCK_POLISY_MAC,
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}
    assert (
        _get_schema_default(result["data_schema"].schema, CONF_HOST)
        == "http://1.2.3.4:8080"
    )

    with (
        patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE),
        patch(
            PATCH_ASYNC_SETUP_ENTRY,
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_IOX_USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"{MOCK_DEVICE_NAME} ({MOCK_HOSTNAME})"
    assert result2["result"].unique_id == MOCK_UUID
    assert result2["data"] == MOCK_IOX_USER_INPUT
    assert len(mock_setup_entry.mock_calls) == 1