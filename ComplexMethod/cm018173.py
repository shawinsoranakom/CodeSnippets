async def test_full_flow(hass: HomeAssistant, mock_account) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.connect",
            return_value=mock_account,
        ),
        patch(
            "homeassistant.components.litterrobot.config_flow.Account.user_id",
            new_callable=PropertyMock,
            return_value=ACCOUNT_USER_ID,
        ),
        patch(
            "homeassistant.components.litterrobot.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG[DOMAIN]
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == CONFIG[DOMAIN][CONF_USERNAME]
    assert result["data"] == CONFIG[DOMAIN]
    assert result["result"].unique_id == ACCOUNT_USER_ID
    assert len(mock_setup_entry.mock_calls) == 1