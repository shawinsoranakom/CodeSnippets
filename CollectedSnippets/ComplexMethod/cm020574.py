async def test_full_user_flow_implementation(
    hass: HomeAssistant,
    mock_elgato: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "127.0.0.1"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.unique_id == "CN11A1A00001"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.1",
        CONF_MAC: None,
    }
    assert not config_entry.options

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_elgato.info.mock_calls) == 1