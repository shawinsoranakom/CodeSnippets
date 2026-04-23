async def test_form(
    hass: HomeAssistant,
    mock_nice_go: AsyncMock,
    mock_setup_entry: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-email",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-email"
    assert result["data"][CONF_EMAIL] == "test-email"
    assert result["data"][CONF_PASSWORD] == "test-password"
    assert result["data"][CONF_REFRESH_TOKEN] == "test-refresh-token"
    assert CONF_REFRESH_TOKEN_CREATION_TIME in result["data"]
    assert result["result"].unique_id == "test-email"
    assert len(mock_setup_entry.mock_calls) == 1