async def test_full_flow_implementation(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_devops_client: AsyncMock,
) -> None:
    """Test registering an integration and finishing flow works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_USER_INPUT,
    )
    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert (
        result2["title"]
        == f"{FIXTURE_USER_INPUT[CONF_ORG]}/{FIXTURE_USER_INPUT[CONF_PROJECT]}"
    )
    assert result2["data"][CONF_ORG] == FIXTURE_USER_INPUT[CONF_ORG]
    assert result2["data"][CONF_PROJECT] == FIXTURE_USER_INPUT[CONF_PROJECT]