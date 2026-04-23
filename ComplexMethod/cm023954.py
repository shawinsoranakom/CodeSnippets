async def form_base(hass: HomeAssistant, advanced: bool) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_USER,
            "show_advanced_options": advanced,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with (
        patch(
            "homeassistant.components.coolmaster.config_flow.CoolMasterNet.status",
            return_value={"test_id": "test_unit"},
        ),
        patch(
            "homeassistant.components.coolmaster.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], _flow_data(advanced)
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "1.1.1.1"
    _expected_data = {
        "host": "1.1.1.1",
        "port": 10102,
        "supported_modes": AVAILABLE_MODES,
        "swing_support": False,
        "send_wakeup_prompt": False,
    }
    if advanced:
        _expected_data["send_wakeup_prompt"] = True
    assert result2["data"] == _expected_data
    assert len(mock_setup_entry.mock_calls) == 1