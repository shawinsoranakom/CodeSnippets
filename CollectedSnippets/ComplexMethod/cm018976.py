async def test_user_flow_can_override_discovery(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test manual user flow can override discovery in progress."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=DISCOVERY_INFO
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm_discovery"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == SOURCE_USER
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCK_HOST,
        },
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["context"]["source"] == SOURCE_USER
    assert result2["data"] == {
        CONF_HOST: MOCK_HOST,
    }
    assert result2["context"]["unique_id"] == "aa:bb:cc:dd:ee:ff"
    assert len(mock_setup_entry.mock_calls) == 1