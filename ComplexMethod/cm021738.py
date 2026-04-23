async def test_dhcp_discovery_starts_user_flow(
    hass: HomeAssistant, config_data: dict[str, str]
) -> None:
    """Test DHCP discovery starts the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_DISCOVERY,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}
    assert result["description_placeholders"] is None

    with (
        patch(
            "homeassistant.components.iaqualink.config_flow.AqualinkClient.login",
            return_value=None,
        ),
        patch(
            "homeassistant.components.iaqualink.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            config_data,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == config_data[CONF_USERNAME]
    assert result["data"] == config_data