async def test_full_flow(
    hass: HomeAssistant,
    mock_c4_account: AsyncMock,
    mock_c4_director: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test full config flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "control4_model_00AA00AA00AA"
    assert result["data"] == {
        CONF_HOST: MOCK_HOST,
        CONF_USERNAME: MOCK_USERNAME,
        CONF_PASSWORD: MOCK_PASSWORD,
        "controller_unique_id": "control4_model_00AA00AA00AA",
    }
    assert result["result"].unique_id == "00:aa:00:aa:00:aa"
    assert len(mock_setup_entry.mock_calls) == 1