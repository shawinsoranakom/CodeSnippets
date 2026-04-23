async def test_full_user_flow_multiple_installations(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_verisure_config_flow: MagicMock,
) -> None:
    """Test a full user initiated configuration flow with multiple installations."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("step_id") == "user"
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    assert result2.get("step_id") == "installation"
    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("errors") is None

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], {"giid": "54321"}
    )
    await hass.async_block_till_done()

    assert result3.get("type") is FlowResultType.CREATE_ENTRY
    assert result3.get("title") == "descending (54321th street)"
    assert result3.get("data") == {
        CONF_GIID: "54321",
        CONF_EMAIL: "verisure_my_pages@example.com",
        CONF_PASSWORD: "SuperS3cr3t!",
    }

    assert len(mock_verisure_config_flow.login.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1