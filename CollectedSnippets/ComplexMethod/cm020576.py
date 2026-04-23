async def test_connection_error(
    hass: HomeAssistant,
    mock_elgato: MagicMock,
) -> None:
    """Test we show user form on Elgato Key Light connection error."""
    mock_elgato.info.side_effect = ElgatoConnectionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "127.0.0.1"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert result["step_id"] == "user"

    # Recover from error
    mock_elgato.info.side_effect = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "127.0.0.2"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.unique_id == "CN11A1A00001"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.2",
        CONF_MAC: None,
    }
    assert not config_entry.options