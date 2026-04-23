async def test_setup_entry(
    hass: HomeAssistant, onboarded, num_entries, num_flows, addon_store_info
) -> None:
    """Test setup of a config entry, including setup of zha."""
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
            "homeassistant.components.onboarding.async_is_onboarded",
            return_value=onboarded,
        ),
        patch(
            "homeassistant.components.homeassistant_yellow.guess_firmware_info",
            return_value=FirmwareInfo(  # Nothing is setup
                device="/dev/ttyAMA1",
                firmware_version=None,
                firmware_type=ApplicationType.EZSP,
                source="unknown",
                owners=[],
            ),
        ),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)

    assert len(mock_get_os_info.mock_calls) == 1

    # Finish setting up ZHA
    if num_entries > 0:
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

    assert len(hass.config_entries.flow.async_progress_by_handler("zha")) == num_flows
    assert len(hass.config_entries.async_entries("zha")) == num_entries

    # Test unloading the config entry
    assert await hass.config_entries.async_unload(config_entry.entry_id)