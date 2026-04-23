async def test_form(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_auth: AsyncMock,
    mock_pydrawise: AsyncMock,
    user: User,
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "asdf@asdf.com",
            CONF_PASSWORD: "__password__",
            CONF_API_KEY: "__api-key__",
        },
    )
    mock_pydrawise.get_user.return_value = user
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "asdf@asdf.com"
    assert result["data"] == {
        CONF_USERNAME: "asdf@asdf.com",
        CONF_PASSWORD: "__password__",
        CONF_API_KEY: "__api-key__",
    }
    assert len(mock_setup_entry.mock_calls) == 1
    mock_auth.check.assert_awaited_once_with()
    mock_pydrawise.get_user.assert_awaited_once_with(fetch_zones=False)