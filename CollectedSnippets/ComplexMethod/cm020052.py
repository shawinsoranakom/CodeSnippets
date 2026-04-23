async def test_reconfigure_add_auth(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Test reconfigure able to add authentication on a simple (no-auth) entry."""
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    result = await config_entry.start_reconfigure_flow(hass)

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert result.get("errors") == {}

    assert CONF_USERNAME not in config_entry.data
    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.system_get_info",
        return_value=SystemInfo(
            **(
                await async_load_json_object_fixture(
                    hass, "system_getInfo.json", DOMAIN
                )
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
        {"next_step_id": "auth"},
    )

    with patch("homeassistant.components.sfr_box.config_flow.SFRBox.authenticate"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "valid",
            },
        )

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reconfigure_successful"
    assert config_entry.data == {
        CONF_HOST: "192.168.0.1",
        CONF_USERNAME: "admin",
        CONF_PASSWORD: "valid",
    }