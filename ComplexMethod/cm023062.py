async def test_full_user_flow(
    hass: HomeAssistant,
    mock_powerfox_local_client: AsyncMock,
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
        user_input={CONF_HOST: MOCK_HOST, CONF_API_KEY: MOCK_API_KEY},
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == f"Poweropti ({MOCK_DEVICE_ID[-5:]})"
    assert result.get("data") == {
        CONF_HOST: MOCK_HOST,
        CONF_API_KEY: MOCK_API_KEY,
    }
    assert result["result"].unique_id == MOCK_DEVICE_ID
    assert len(mock_powerfox_local_client.value.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1