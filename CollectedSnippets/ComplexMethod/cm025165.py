def async_start_setup(
    hass: core.HomeAssistant,
    integration: str,
    phase: SetupPhases,
    group: str | None = None,
) -> Generator[None]:
    """Keep track of when setup starts and finishes.

    :param hass: Home Assistant instance
    :param integration: The integration that is being setup
    :param phase: The phase of setup
    :param group: The group (config entry/platform instance) that is being setup

      A group is a group of setups that run in parallel.

    """
    if hass.is_stopping or hass.state is core.CoreState.running:
        # Don't track setup times when we are shutting down or already running
        # as we present the timings as "Integration startup time", and we
        # don't want to add all the setup retry times to that.
        yield
        return

    setup_started = _setup_started(hass)
    current = (integration, group)
    if current in setup_started:
        # We are already inside another async_start_setup, this like means we
        # are setting up a platform inside async_setup_entry so we should not
        # record this as a new setup
        yield
        return

    started = time.monotonic()
    current_setup_group.set(current)
    setup_started[current] = started

    try:
        yield
    finally:
        time_taken = time.monotonic() - started
        del setup_started[current]
        group_setup_times = _setup_times(hass)[integration][group]
        # We may see the phase multiple times if there are multiple
        # platforms, but we only care about the longest time.
        group_setup_times[phase] = max(group_setup_times[phase], time_taken)
        if group is None:
            _LOGGER.info(
                "Setup of domain %s took %.2f seconds", integration, time_taken
            )
        elif _LOGGER.isEnabledFor(logging.DEBUG):
            wait_time = -sum(value for value in group_setup_times.values() if value < 0)
            calculated_time = time_taken - wait_time
            _LOGGER.debug(
                "Phase %s for %s (%s) took %.2fs (elapsed=%.2fs) (wait_time=%.2fs)",
                phase,
                integration,
                group,
                calculated_time,
                time_taken,
                wait_time,
            )