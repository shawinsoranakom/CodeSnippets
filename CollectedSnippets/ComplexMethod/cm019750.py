async def test_full_user_flow_single_installation(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_verisure_config_flow: MagicMock,
) -> None:
    """Test a full user initiated configuration flow with a single installation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("step_id") == "user"
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {}

    mock_verisure_config_flow.get_installations.return_value = {
        k1: {k2: {k3: [v3[0]] for k3, v3 in v2.items()} for k2, v2 in v1.items()}
        for k1, v1 in mock_verisure_config_flow.get_installations.return_value.items()
    }

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    assert result2.get("type") is FlowResultType.CREATE_ENTRY
    assert result2.get("title") == "ascending (12345th street)"
    assert result2.get("data") == {
        CONF_GIID: "12345",
        CONF_EMAIL: "verisure_my_pages@example.com",
        CONF_PASSWORD: "SuperS3cr3t!",
    }

    assert len(mock_verisure_config_flow.login.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1