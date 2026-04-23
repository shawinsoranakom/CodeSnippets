async def test_dhcp_can_confirm(hass: HomeAssistant) -> None:
    """Test DHCP discovery flow can confirm right away."""

    with patch(
        "homeassistant.components.emonitor.config_flow.Emonitor.async_get_status",
        return_value=_mock_emonitor(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DHCP_SERVICE_INFO,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        "host": "1.2.3.4",
        "name": "Emonitor DDEEFF",
    }

    with patch(
        "homeassistant.components.emonitor.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Emonitor DDEEFF"
    assert result2["data"] == {
        "host": "1.2.3.4",
    }
    assert len(mock_setup_entry.mock_calls) == 1