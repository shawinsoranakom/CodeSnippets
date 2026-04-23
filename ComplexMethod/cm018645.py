async def test_zeroconf_form(
    hass: HomeAssistant, zeroconf_payload: ZeroconfServiceInfo
) -> None:
    """Test we pass Zeroconf discoveries to the manager."""

    mock_manager = hass.data[DATA_SONOS_DISCOVERY_MANAGER] = MagicMock()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=zeroconf_payload,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with (
        patch(
            "homeassistant.components.sonos.async_setup",
            return_value=True,
        ) as mock_setup,
        patch(
            "homeassistant.components.sonos.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Sonos"
    assert result2["data"] == {}

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_manager.mock_calls) == 2