async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_tailwind: MagicMock,
    side_effect: Exception,
    expected_error: dict[str, str],
) -> None:
    """Test we show user form on a connection error."""
    mock_tailwind.status.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_HOST: "127.0.0.1",
            CONF_TOKEN: "987654",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == expected_error

    mock_tailwind.status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.2",
            CONF_TOKEN: "123456",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.unique_id == "3c:e9:0e:6d:21:84"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.2",
        CONF_TOKEN: "123456",
    }
    assert not config_entry.options