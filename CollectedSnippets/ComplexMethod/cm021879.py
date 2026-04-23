async def test_reauth_flow(hass: HomeAssistant) -> None:
    """Test reauth flow re-registers and updates the auth token."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="ABC123",
        data={HMIPC_HAPID: "ABC123", HMIPC_AUTHTOKEN: "old_token", HMIPC_NAME: "hmip"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Submit reauth_confirm, button not yet pressed -> link form shown
    with (
        patch(
            "homeassistant.components.homematicip_cloud.hap.HomematicipAuth.async_setup",
            return_value=True,
        ),
        patch(
            "homeassistant.components.homematicip_cloud.hap.HomematicipAuth.async_checkbutton",
            return_value=False,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"
    assert result["errors"] == {"base": "press_the_button"}

    # User presses button -> reauth completes
    with (
        patch(
            "homeassistant.components.homematicip_cloud.hap.HomematicipAuth.async_checkbutton",
            return_value=True,
        ),
        patch(
            "homeassistant.components.homematicip_cloud.hap.HomematicipAuth.async_register",
            return_value="new_token",
        ),
        patch(
            "homeassistant.components.homematicip_cloud.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.homematicip_cloud.async_unload_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[HMIPC_AUTHTOKEN] == "new_token"