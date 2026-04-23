async def test_user(hass: HomeAssistant) -> None:
    """Test user flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            return_value=mock_uptimerobot_api_response(
                api_path=API_PATH_USER_ME, data=MOCK_UPTIMEROBOT_ACCOUNT
            ),
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY},
        )
        await hass.async_block_till_done()

    assert result2["result"].unique_id == MOCK_UPTIMEROBOT_EMAIL
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == MOCK_UPTIMEROBOT_ACCOUNT["email"]
    assert result2["data"] == {CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY}
    assert len(mock_setup_entry.mock_calls) == 1