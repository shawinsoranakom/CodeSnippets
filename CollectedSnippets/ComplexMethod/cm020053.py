async def test_reconfigure_clear_auth(
    hass: HomeAssistant, config_entry_with_auth: ConfigEntry
) -> None:
    """Test reconfigure clears authentication on an entry with auth."""
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    result = await config_entry_with_auth.start_reconfigure_flow(hass)

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert result.get("errors") == {}

    assert config_entry_with_auth.data[CONF_USERNAME] == "admin"
    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=SystemInfo(
            **(
                await async_load_json_object_fixture(
                    hass, "system_getInfo.json", DOMAIN
                )
                | {"mac_addr": "e4:5d:51:00:11:23"}
            )
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "192.168.0.1",
            },
        )

    assert result.get("type") is FlowResultType.MENU
    assert result.get("step_id") == "choose_auth"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "skip_auth"},
    )

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reconfigure_successful"
    assert CONF_USERNAME not in config_entry_with_auth.data