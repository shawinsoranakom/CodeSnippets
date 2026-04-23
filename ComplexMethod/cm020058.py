async def test_form_reauth_with_new_username(
    hass: HomeAssistant, cloud_config_entry: MockConfigEntry
) -> None:
    """Test reauthenticate with new username."""

    result = await cloud_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

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
            "homeassistant.components.risco.config_flow.RiscoCloud.close",
        ),
        patch(
            "homeassistant.components.risco.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**TEST_CLOUD_DATA, CONF_USERNAME: "new_user"}
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert cloud_config_entry.data[CONF_USERNAME] == "new_user"
    assert cloud_config_entry.unique_id == "new_user"
    assert len(mock_setup_entry.mock_calls) == 1