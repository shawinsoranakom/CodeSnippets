async def test_config_flow_skip_auth(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test user flow (no authentication)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

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

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "choose_auth"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "skip_auth"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "SFR Box"
    assert result["data"] == {CONF_HOST: "192.168.0.1"}
    assert result["context"]["unique_id"] == "e4:5d:51:00:11:22"

    assert len(mock_setup_entry.mock_calls) == 1