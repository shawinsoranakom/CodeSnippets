async def test_user_flow_invalid_mac(hass: HomeAssistant) -> None:
    """Test we handle invalid mac address."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.eq3btsmart.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_MAC: "invalid"},
        )
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {CONF_MAC: "invalid_mac_address"}
        assert len(mock_setup_entry.mock_calls) == 0

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_MAC: MAC},
        )
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == slugify(MAC)
        assert result["data"] == {}
        assert result["context"]["unique_id"] == MAC
        assert len(mock_setup_entry.mock_calls) == 1