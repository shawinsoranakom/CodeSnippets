async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_peblar: MagicMock,
    side_effect: Exception,
    expected_error: dict[str, str],
) -> None:
    """Test we show user form on a connection error."""
    mock_peblar.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "OMGCATS!",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == expected_error

    mock_peblar.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.2",
            CONF_PASSWORD: "OMGPUPPIES!",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.unique_id == "23-45-A4O-MOF"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.2",
        CONF_PASSWORD: "OMGPUPPIES!",
    }
    assert not config_entry.options