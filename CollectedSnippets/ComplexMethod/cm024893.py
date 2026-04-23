async def test_webhook_reconfigure_cloudhook(
    hass: HomeAssistant, webhook_flow_conf: None
) -> None:
    """Test reconfigure updates to cloudhook if subscribed."""
    assert await setup.async_setup_component(hass, "cloud", {})

    config_entry = MockConfigEntry(
        domain="test_single", data={"webhook_id": "12345", "cloudhook": False}
    )
    config_entry.add_to_hass(hass)

    flow = config_entries.HANDLERS["test_single"]()
    flow.hass = hass
    flow.context = {
        "source": config_entries.SOURCE_RECONFIGURE,
        "entry_id": config_entry.entry_id,
    }

    result = await flow.async_step_reconfigure()
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

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
        result = await flow.async_step_reconfigure(user_input={})

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert result["description_placeholders"] == {"webhook_url": "https://example.com"}
    assert len(mock_create.mock_calls) == 1

    assert config_entry.data["webhook_id"] == "12345"
    assert config_entry.data["cloudhook"] is True