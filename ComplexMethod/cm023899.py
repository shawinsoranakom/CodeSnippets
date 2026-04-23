async def test_no_repositories(
    hass: HomeAssistant,
    mock_setup_entry: None,
    github_device_client: AsyncMock,
    github_client: AsyncMock,
    device_activation_event: asyncio.Event,
) -> None:
    """Test the full manual user flow from start to finish."""

    github_client.user.repos.side_effect = [MagicMock(is_last_page=True, data=[])]
    github_client.user.starred.side_effect = [MagicMock(is_last_page=True, data=[])]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["step_id"] == "device"
    assert result["type"] is FlowResultType.SHOW_PROGRESS

    device_activation_event.set()
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["step_id"] == "repositories"
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    schema = result["data_schema"]
    repositories = schema.schema[CONF_REPOSITORIES].options
    assert len(repositories) == 2

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_REPOSITORIES: DEFAULT_REPOSITORIES}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY