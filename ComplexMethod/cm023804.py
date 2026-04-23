async def test_discovered_by_dhcp_or_integration_discovery(
    hass: HomeAssistant, source, data, bulb_type, extended_white_range, name
) -> None:
    """Test we can configure when discovered from dhcp or discovery."""
    with _patch_wizlight(
        device=None, extended_white_range=extended_white_range, bulb_type=bulb_type
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": source}, data=data
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"

    with (
        _patch_wizlight(
            device=None, extended_white_range=extended_white_range, bulb_type=bulb_type
        ),
        patch(
            "homeassistant.components.wiz.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.wiz.async_setup", return_value=True
        ) as mock_setup,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == name
    assert result2["data"] == {
        CONF_HOST: "1.1.1.1",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1