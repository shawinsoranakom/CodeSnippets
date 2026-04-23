async def test_setup_zha(hass: HomeAssistant, addon_store_info) -> None:
    """Test zha gets the right config."""
    mock_integration(hass, MockModule("hassio"))
    await async_setup_component(hass, HASSIO_DOMAIN, {})

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={"firmware": ApplicationType.EZSP},
        domain=DOMAIN,
        options={},
        title="Home Assistant Yellow",
        version=1,
        minor_version=2,
    )
    config_entry.add_to_hass(hass)
    with (
        patch(
            "homeassistant.components.homeassistant_yellow.get_os_info",
            return_value={"board": "yellow"},
        ) as mock_get_os_info,
        patch(
            "homeassistant.components.onboarding.async_is_onboarded", return_value=False
        ),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(mock_get_os_info.mock_calls) == 1

    # Finish setting up ZHA
    zha_flows = hass.config_entries.flow.async_progress_by_handler("zha")
    assert len(zha_flows) == 1
    assert zha_flows[0]["step_id"] == "choose_setup_strategy"

    setup_result = await hass.config_entries.flow.async_configure(
        zha_flows[0]["flow_id"],
        user_input={"next_step_id": zha.config_flow.SETUP_STRATEGY_ADVANCED},
    )
    assert setup_result["step_id"] == "choose_formation_strategy"

    await hass.config_entries.flow.async_configure(
        setup_result["flow_id"],
        user_input={"next_step_id": zha.config_flow.FORMATION_REUSE_SETTINGS},
    )
    await hass.async_block_till_done()

    config_entry = hass.config_entries.async_entries("zha")[0]
    assert config_entry.data == {
        "device": {
            "baudrate": 115200,
            "flow_control": "hardware",
            "path": "/dev/ttyAMA1",
        },
        "radio_type": "ezsp",
    }
    assert config_entry.options == {}
    assert config_entry.title == "Yellow"