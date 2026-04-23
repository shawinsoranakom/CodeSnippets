async def test_user_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, player_mocks: PlayerMocks
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "player-name1111"
    assert result["data"] == {CONF_HOST: "1.1.1.1", CONF_PORT: 11000}
    assert result["result"].unique_id == "ff:ff:01:01:01:01-11000"

    mock_setup_entry.assert_called_once()