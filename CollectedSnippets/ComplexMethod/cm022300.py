async def test_dhcp_can_confirm(hass: HomeAssistant) -> None:
    """Test DHCP discovery flow can confirm right away."""

    with patch(
        "homeassistant.components.radiotherm.data.radiotherm.get_thermostat",
        return_value=_mock_radiotherm(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                hostname="radiotherm",
                ip="1.2.3.4",
                macaddress="aabbccddeeff",
            ),
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        "host": "1.2.3.4",
        "name": "My Name",
        "model": "Model",
    }

    with patch(
        "homeassistant.components.radiotherm.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "My Name"
    assert result2["data"] == {
        "host": "1.2.3.4",
    }
    assert len(mock_setup_entry.mock_calls) == 1