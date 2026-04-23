async def test_form_user_reauth(hass: HomeAssistant) -> None:
    """Test reauth."""
    entry = mock_config_entry()
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert "flow_id" in flows[0]

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with RuckusAjaxApiPatchContext():
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "new_name",
                CONF_PASSWORD: "new_pass",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"