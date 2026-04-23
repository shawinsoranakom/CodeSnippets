async def test_full_flow(
    hass: HomeAssistant,
    mock_vilfo_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_is_valid_host: AsyncMock,
    user_input: dict[str, Any],
    expected_unique_id: str,
    mac: str | None,
) -> None:
    """Test we can finish a config flow."""

    mock_vilfo_client.resolve_mac_address.return_value = mac
    mock_vilfo_client.mac = mac

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == user_input[CONF_HOST]
    assert result["data"] == user_input
    assert result["result"].unique_id == expected_unique_id

    assert len(mock_setup_entry.mock_calls) == 1