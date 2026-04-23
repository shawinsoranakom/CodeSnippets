async def _async_set_up_integrations(
    hass: core.HomeAssistant, config: dict[str, Any]
) -> None:
    """Set up all the integrations."""
    watcher = _WatchPendingSetups(hass, _setup_started(hass))
    watcher.async_start()

    integrations, all_integrations = await _async_resolve_domains_and_preload(
        hass, config
    )
    # Detect all cycles
    integrations_after_dependencies = (
        await loader.resolve_integrations_after_dependencies(
            hass, all_integrations.values(), set(all_integrations)
        )
    )
    all_domains = set(integrations_after_dependencies)
    domains = set(integrations) & all_domains

    _LOGGER.info(
        "Domains to be set up: %s\nDependencies: %s",
        domains or "{}",
        (all_domains - domains) or "{}",
    )

    async_set_domains_to_be_loaded(hass, all_domains)

    # Initialize recorder
    if "recorder" in all_domains:
        recorder.async_initialize_recorder(hass)

    stages: list[tuple[str, set[str], int | None]] = [
        *(
            (name, domain_group, timeout)
            for name, domain_group, timeout in STAGE_0_INTEGRATIONS
        ),
        ("1", STAGE_1_INTEGRATIONS, STAGE_1_TIMEOUT),
        ("2", domains, STAGE_2_TIMEOUT),
    ]

    _LOGGER.info("Setting up stage 0")
    for name, domain_group, timeout in stages:
        stage_domains_unfiltered = domain_group & all_domains
        if not stage_domains_unfiltered:
            _LOGGER.info("Nothing to set up in stage %s: %s", name, domain_group)
            continue

        stage_domains = stage_domains_unfiltered - hass.config.components
        if not stage_domains:
            _LOGGER.info("Already set up stage %s: %s", name, stage_domains_unfiltered)
            continue

        stage_dep_domains_unfiltered = {
            dep
            for domain in stage_domains
            for dep in integrations_after_dependencies[domain]
            if dep not in stage_domains
        }
        stage_dep_domains = stage_dep_domains_unfiltered - hass.config.components

        stage_all_domains = stage_domains | stage_dep_domains

        _LOGGER.info(
            "Setting up stage %s: %s; already set up: %s\n"
            "Dependencies: %s; already set up: %s",
            name,
            stage_domains,
            (stage_domains_unfiltered - stage_domains) or "{}",
            stage_dep_domains or "{}",
            (stage_dep_domains_unfiltered - stage_dep_domains) or "{}",
        )

        if timeout is None:
            await _async_setup_multi_components(hass, stage_all_domains, config)
            continue
        try:
            async with hass.timeout.async_timeout(
                timeout,
                cool_down=COOLDOWN_TIME,
                cancel_message=f"Bootstrap stage {name} timeout",
            ):
                await _async_setup_multi_components(hass, stage_all_domains, config)
        except TimeoutError:
            _LOGGER.warning(
                "Setup timed out for stage %s waiting on %s - moving forward",
                name,
                hass._active_tasks,  # noqa: SLF001
            )

    # Wrap up startup
    _LOGGER.debug("Waiting for startup to wrap up")
    try:
        async with hass.timeout.async_timeout(
            WRAP_UP_TIMEOUT,
            cool_down=COOLDOWN_TIME,
            cancel_message="Bootstrap startup wrap up timeout",
        ):
            await hass.async_block_till_done()
    except TimeoutError:
        _LOGGER.warning(
            "Setup timed out for bootstrap waiting on %s - moving forward",
            hass._active_tasks,  # noqa: SLF001
        )

    watcher.async_stop()

    if _LOGGER.isEnabledFor(logging.DEBUG):
        setup_time = async_get_setup_timings(hass)
        _LOGGER.debug(
            "Integration setup times: %s",
            dict(sorted(setup_time.items(), key=itemgetter(1), reverse=True)),
        )