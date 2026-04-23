async def test_full_local_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_geniushub_client: AsyncMock,
) -> None:
    """Test full local flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "local_api"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "local_api"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "10.0.0.130",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "10.0.0.130"
    assert result["data"] == {
        CONF_HOST: "10.0.0.130",
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
    }
    assert result["result"].unique_id == "aa:bb:cc:dd:ee:ff"