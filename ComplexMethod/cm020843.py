async def test_options_flow_incorrect_username(
    hass: HomeAssistant,
    setup_integration: ComponentSetup,
    config_entry: MockConfigEntry,
    default_user: MockUser,
) -> None:
    """Test updating options doesn't work with incorrect username."""
    await setup_integration(config_entry, default_user)
    with patch("pylast.User", return_value=default_user):
        entry = hass.config_entries.async_entries(DOMAIN)[0]
        result = await hass.config_entries.options.async_init(entry.entry_id)
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

    with patch(
        "pylast.User",
        return_value=MockUser(
            thrown_error=WSError("network", "status", "User not found")
        ),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_USERS: [USERNAME_1]},
        )
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"
        assert result["errors"]["base"] == "invalid_account"

    with patch("pylast.User", return_value=default_user):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_USERS: [USERNAME_1]},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_API_KEY: API_KEY,
        CONF_MAIN_USER: USERNAME_1,
        CONF_USERS: [USERNAME_1],
    }