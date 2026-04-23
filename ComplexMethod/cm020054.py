async def test_reconfigure_mismatch(
    hass: HomeAssistant, config_entry_with_auth: ConfigEntry
) -> None:
    """Test reconfigure fails if the unique ID (=MAC) does not match."""
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
            )
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "192.168.0.1",
            },
        )

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "unique_id_mismatch"