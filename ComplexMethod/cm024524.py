async def test_manual_flow_works(
    hass: HomeAssistant,
    mock_homewizardenergy: MagicMock,
    mock_setup_entry: AsyncMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test config flow accepts user configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_IP_ADDRESS: "2.2.2.2"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result == snapshot

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_homewizardenergy.close.mock_calls) == 1
    assert len(mock_homewizardenergy.device.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1