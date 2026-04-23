async def _async_setup_component(
    hass: core.HomeAssistant, domain: str, config: ConfigType
) -> bool:
    """Set up a component for Home Assistant.

    This method is a coroutine.
    """
    try:
        integration = await loader.async_get_integration(hass, domain)
    except loader.IntegrationNotFound:
        _log_error_setup_error(hass, domain, None, "Integration not found.")
        if not hass.config.safe_mode and hass.config_entries.async_entries(domain):
            ir.async_create_issue(
                hass,
                HOMEASSISTANT_DOMAIN,
                f"integration_not_found.{domain}",
                is_fixable=True,
                issue_domain=HOMEASSISTANT_DOMAIN,
                severity=IssueSeverity.ERROR,
                translation_key="integration_not_found",
                translation_placeholders={
                    "domain": domain,
                },
                data={"domain": domain},
            )
        return False

    log_error = partial(_log_error_setup_error, hass, domain, integration)

    if integration.disabled:
        log_error(f"Dependency is disabled - {integration.disabled}")
        return False

    integration_set = {domain}

    load_translations_task: asyncio.Task[None] | None = None
    if integration.has_translations and not translation.async_translations_loaded(
        hass, integration_set
    ):
        # For most cases we expect the translations are already
        # loaded since we try to load them in bootstrap ahead of time.
        # If for some reason the background task in bootstrap was too slow
        # or the integration was added after bootstrap, we will load them here.
        load_translations_task = create_eager_task(
            translation.async_load_integrations(hass, integration_set), loop=hass.loop
        )
    # Validate all dependencies exist and there are no circular dependencies
    if await integration.resolve_dependencies() is None:
        return False

    # Process requirements as soon as possible, so we can import the component
    # without requiring imports to be in functions.
    try:
        await async_process_deps_reqs(hass, config, integration)
    except HomeAssistantError as err:
        log_error(str(err))
        return False

    # Some integrations fail on import because they call functions incorrectly.
    # So we do it before validating config to catch these errors.
    try:
        component = await integration.async_get_component()
    except ImportError as err:
        log_error(f"Unable to import component: {err}", err)
        return False

    integration_config_info = await conf_util.async_process_component_config(
        hass, config, integration, component
    )
    conf_util.async_handle_component_errors(hass, integration_config_info, integration)
    processed_config = conf_util.async_drop_config_annotations(
        integration_config_info, integration
    )
    for platform_exception in integration_config_info.exception_info_list:
        if platform_exception.translation_key not in NOTIFY_FOR_TRANSLATION_KEYS:
            continue
        async_notify_setup_error(
            hass, platform_exception.platform_path, platform_exception.integration_link
        )
    if processed_config is None:
        log_error("Invalid config.")
        return False

    # Detect attempt to setup integration which can be setup only from config entry
    if (
        domain in processed_config
        and not hasattr(component, "async_setup")
        and not hasattr(component, "setup")
        and not hasattr(component, "CONFIG_SCHEMA")
    ):
        _LOGGER.error(
            (
                "The '%s' integration does not support YAML setup, please remove it "
                "from your configuration"
            ),
            domain,
        )
        async_create_issue(
            hass,
            HOMEASSISTANT_DOMAIN,
            f"config_entry_only_{domain}",
            is_fixable=False,
            severity=IssueSeverity.ERROR,
            issue_domain=domain,
            translation_key="config_entry_only",
            translation_placeholders={
                "domain": domain,
                "add_integration": f"/config/integrations/dashboard/add?domain={domain}",
            },
        )

    _LOGGER.info("Setting up %s", domain)

    with async_start_setup(hass, integration=domain, phase=SetupPhases.SETUP):
        if hasattr(component, "PLATFORM_SCHEMA"):
            # Entity components have their own warning
            warn_task = None
        else:
            warn_task = hass.loop.call_later(
                SLOW_SETUP_WARNING,
                _LOGGER.warning,
                "Setup of %s is taking over %s seconds.",
                domain,
                SLOW_SETUP_WARNING,
            )

        task: Awaitable[bool] | None = None
        result: Any | bool = True
        try:
            if hasattr(component, "async_setup"):
                task = component.async_setup(hass, processed_config)
            elif hasattr(component, "setup"):
                # This should not be replaced with hass.async_add_executor_job because
                # we don't want to track this task in case it blocks startup.
                task = hass.loop.run_in_executor(
                    None, component.setup, hass, processed_config
                )
            elif not hasattr(component, "async_setup_entry"):
                log_error("No setup or config entry setup function defined.")
                return False

            if task:
                async with hass.timeout.async_timeout(SLOW_SETUP_MAX_WAIT, domain):
                    result = await task
        except TimeoutError:
            _LOGGER.error(
                (
                    "Setup of '%s' is taking longer than %s seconds."
                    " Startup will proceed without waiting any longer"
                ),
                domain,
                SLOW_SETUP_MAX_WAIT,
            )
            return False
        # pylint: disable-next=broad-except
        except (asyncio.CancelledError, SystemExit, Exception) as exc:
            _LOGGER.exception("Error during setup of component %s: %s", domain, exc)  # noqa: TRY401
            async_notify_setup_error(hass, domain, integration.documentation)
            return False
        finally:
            if warn_task:
                warn_task.cancel()
        if result is False:
            log_error("Integration failed to initialize.")
            return False
        if result is not True:
            log_error(
                f"Integration {domain!r} did not return boolean if setup was "
                "successful. Disabling component."
            )
            return False

        if load_translations_task:
            await load_translations_task

    if integration.platforms_exists(("config_flow",)):
        # If the integration has a config_flow, wait for import flows.
        # As these are all created with eager tasks, we do not sleep here,
        # as the tasks will always be started before we reach this point.
        await hass.config_entries.flow.async_wait_import_flow_initialized(domain)

    # Add to components before the entry.async_setup
    # call to avoid a deadlock when forwarding platforms
    hass.config.components.add(domain)

    if entries := hass.config_entries.async_entries(
        domain, include_ignore=False, include_disabled=False
    ):
        await asyncio.gather(
            *(
                create_eager_task(
                    entry.async_setup_locked(hass, integration=integration),
                    name=(
                        f"config entry setup {entry.title} {entry.domain} "
                        f"{entry.entry_id}"
                    ),
                    loop=hass.loop,
                )
                for entry in entries
            )
        )

    # Cleanup
    hass.data[_DATA_SETUP].pop(domain, None)

    hass.bus.async_fire_internal(
        EVENT_COMPONENT_LOADED, EventComponentLoaded(component=domain)
    )

    return True