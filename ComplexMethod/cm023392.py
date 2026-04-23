async def test_full_user_flow(
    hass: HomeAssistant,
    mock_autarco_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert not result.get("errors")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@autarco.com", CONF_PASSWORD: "test-password"},
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "test@autarco.com"
    assert result.get("data") == {
        CONF_EMAIL: "test@autarco.com",
        CONF_PASSWORD: "test-password",
    }
    assert len(mock_autarco_client.get_account.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1