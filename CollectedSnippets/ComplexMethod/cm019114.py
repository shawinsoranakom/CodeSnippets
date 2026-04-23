async def test_on_connect_failed(hass: HomeAssistant) -> None:
    """Test when we have errors connecting the router."""
    flow_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER, "show_advanced_options": True},
    )

    with patch(CONNECT_METHOD, return_value=(None, "Error")):
        result = await hass.config_entries.flow.async_configure(
            flow_result["flow_id"], user_input=CONFIG_ADB_SERVER
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}

    with patch(
        CONNECT_METHOD,
        side_effect=TypeError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONFIG_ADB_SERVER
        )
        assert result2["type"] is FlowResultType.FORM
        assert result2["errors"] == {"base": "unknown"}

    with (
        patch(
            CONNECT_METHOD,
            return_value=(MockConfigDevice(), None),
        ),
        PATCH_SETUP_ENTRY,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], user_input=CONFIG_ADB_SERVER
        )
        await hass.async_block_till_done()

        assert result3["type"] is FlowResultType.CREATE_ENTRY
        assert result3["title"] == HOST
        assert result3["data"] == CONFIG_ADB_SERVER