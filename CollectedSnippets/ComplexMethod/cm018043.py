async def test_async_start_setup_config_entry(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test setup started keeps track of setup times with a config entry."""
    hass.set_state(CoreState.not_running)
    setup_started = hass.data.setdefault(setup._DATA_SETUP_STARTED, {})
    setup_time = setup._setup_times(hass)

    with setup.async_start_setup(
        hass, integration="august", phase=setup.SetupPhases.SETUP
    ):
        assert isinstance(setup_started[("august", None)], float)

    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id",
        phase=setup.SetupPhases.CONFIG_ENTRY_SETUP,
    ):
        assert isinstance(setup_started[("august", "entry_id")], float)
        with setup.async_start_setup(
            hass,
            integration="august",
            group="entry_id",
            phase=setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP,
        ):
            assert isinstance(setup_started[("august", "entry_id")], float)

    # CONFIG_ENTRY_PLATFORM_SETUP inside of CONFIG_ENTRY_SETUP should not be tracked
    assert setup_time["august"] == {
        None: {setup.SetupPhases.SETUP: ANY},
        "entry_id": {setup.SetupPhases.CONFIG_ENTRY_SETUP: ANY},
    }
    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id",
        phase=setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP,
    ):
        assert isinstance(setup_started[("august", "entry_id")], float)

    # Platforms outside of CONFIG_ENTRY_SETUP should be tracked
    # This simulates a late platform forward
    assert setup_time["august"] == {
        None: {setup.SetupPhases.SETUP: ANY},
        "entry_id": {
            setup.SetupPhases.CONFIG_ENTRY_SETUP: ANY,
            setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP: ANY,
        },
    }

    shorter_time = setup_time["august"]["entry_id"][
        setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP
    ]
    # Setup another platform, but make it take longer
    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id",
        phase=setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP,
    ):
        freezer.tick(10)
        assert isinstance(setup_started[("august", "entry_id")], float)

    longer_time = setup_time["august"]["entry_id"][
        setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP
    ]
    assert longer_time > shorter_time
    # Setup another platform, but make it take shorter
    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id",
        phase=setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP,
    ):
        assert isinstance(setup_started[("august", "entry_id")], float)

    # Ensure we keep the longest time
    assert (
        setup_time["august"]["entry_id"][setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP]
        == longer_time
    )

    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id2",
        phase=setup.SetupPhases.CONFIG_ENTRY_SETUP,
    ):
        assert isinstance(setup_started[("august", "entry_id2")], float)
        # We wrap places where we wait for other components
        # or the import of a module with async_freeze_setup
        # so we can subtract the time waited from the total setup time
        with setup.async_pause_setup(hass, setup.SetupPhases.WAIT_BASE_PLATFORM_SETUP):
            await asyncio.sleep(0)

    # Wait time should be added if freeze_setup is used
    assert setup_time["august"] == {
        None: {setup.SetupPhases.SETUP: ANY},
        "entry_id": {
            setup.SetupPhases.CONFIG_ENTRY_SETUP: ANY,
            setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP: ANY,
        },
        "entry_id2": {
            setup.SetupPhases.CONFIG_ENTRY_SETUP: ANY,
            setup.SetupPhases.WAIT_BASE_PLATFORM_SETUP: ANY,
        },
    }