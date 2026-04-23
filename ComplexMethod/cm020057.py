async def test_cloud_form(hass: HomeAssistant) -> None:
    """Test we get the cloud form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "cloud"}
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {}

    with (
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.login",
            return_value=True,
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.site_name",
            new_callable=PropertyMock(return_value=TEST_SITE_NAME),
        ),
        patch(
            "homeassistant.components.risco.config_flow.RiscoCloud.close"
        ) as mock_close,
        patch(
            "homeassistant.components.risco.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], TEST_CLOUD_DATA
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == TEST_SITE_NAME
    assert result3["data"] == TEST_CLOUD_DATA
    assert len(mock_setup_entry.mock_calls) == 1
    mock_close.assert_awaited_once()