async def test_webhook_create_cloudhook(
    hass: HomeAssistant, webhook_flow_conf: None
) -> None:
    """Test cloudhook will be created if subscribed."""
    assert await setup.async_setup_component(hass, "cloud", {})

    async_setup_entry = Mock(return_value=True)
    async_unload_entry = Mock(return_value=True)

    mock_integration(
        hass,
        MockModule(
            "test_single",
            async_setup_entry=async_setup_entry,
            async_unload_entry=async_unload_entry,
            async_remove_entry=config_entry_flow.webhook_async_remove_entry,
        ),
    )
    mock_platform(hass, "test_single.config_flow", None)

    result = await hass.config_entries.flow.async_init(
        "test_single", context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    with (
        patch(
            "hass_nabucasa.cloudhooks.Cloudhooks.async_create",
            return_value={"cloudhook_url": "https://example.com"},
        ) as mock_create,
        patch(
            "hass_nabucasa.Cloud.subscription_expired",
            new_callable=PropertyMock(return_value=False),
        ),
        patch(
            "hass_nabucasa.Cloud.is_logged_in",
            new_callable=PropertyMock(return_value=True),
        ),
        patch(
            "hass_nabucasa.iot_base.BaseIoT.connected",
            new_callable=PropertyMock(return_value=True),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["description_placeholders"]["webhook_url"] == "https://example.com"
    assert len(mock_create.mock_calls) == 1
    assert len(async_setup_entry.mock_calls) == 1

    with patch(
        "hass_nabucasa.cloudhooks.Cloudhooks.async_delete",
        return_value={"cloudhook_url": "https://example.com"},
    ) as mock_delete:
        result = await hass.config_entries.async_remove(result["result"].entry_id)

    assert len(mock_delete.mock_calls) == 1
    assert result["require_restart"] is False
    await hass.async_block_till_done()