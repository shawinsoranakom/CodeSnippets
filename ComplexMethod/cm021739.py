async def test_reauth_success(hass: HomeAssistant, config_data: dict[str, str]) -> None:
    """Test successful reauthentication."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=config_data[CONF_USERNAME],
        data=config_data,
    )
    entry.add_to_hass(hass)

    new_username = "updated@example.com"

    result = await entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.iaqualink.config_flow.AqualinkClient.login",
            return_value=None,
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_reload",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: new_username, CONF_PASSWORD: "new_password"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.title == new_username
    assert dict(entry.data) == {
        **config_data,
        CONF_USERNAME: new_username,
        CONF_PASSWORD: "new_password",
    }