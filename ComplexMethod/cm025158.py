async def _async_resolve_domains_and_preload(
    hass: core.HomeAssistant, config: dict[str, Any]
) -> tuple[dict[str, Integration], dict[str, Integration]]:
    """Resolve all dependencies and return integrations to set up.

    The return value is a tuple of two dictionaries:
    - The first dictionary contains integrations
      specified by the configuration (including config entries).
    - The second dictionary contains the same integrations as the first dictionary
      together with all their dependencies.
    """
    domains_to_setup = _get_domains(hass, config)

    # Also process all base platforms since we do not require the manifest
    # to list them as dependencies.
    # We want to later avoid lock contention when multiple integrations try to load
    # their manifests at once.
    #
    # Additionally process integrations that are defined under base platforms
    # to speed things up.
    # For example if we have
    # sensor:
    #   - platform: template
    #
    # `template` has to be loaded to validate the config for sensor.
    # The more platforms under `sensor:`, the longer
    # it will take to finish setup for `sensor` because each of these
    # platforms has to be imported before we can validate the config.
    #
    # Thankfully we are migrating away from the platform pattern
    # so this will be less of a problem in the future.
    platform_integrations = conf_util.extract_platform_integrations(
        config, BASE_PLATFORMS
    )
    additional_domains_to_process = {
        *BASE_PLATFORMS,
        *chain.from_iterable(platform_integrations.values()),
    }

    # Resolve all dependencies so we know all integrations
    # that will have to be loaded and start right-away
    integrations_or_excs = await loader.async_get_integrations(
        hass, {*domains_to_setup, *additional_domains_to_process}
    )
    # Eliminate those missing or with invalid manifest
    integrations_to_process = {
        domain: itg
        for domain, itg in integrations_or_excs.items()
        if isinstance(itg, Integration)
    }
    integrations_dependencies = await loader.resolve_integrations_dependencies(
        hass, integrations_to_process.values()
    )
    # Eliminate those without valid dependencies
    integrations_to_process = {
        domain: integrations_to_process[domain] for domain in integrations_dependencies
    }

    integrations_to_setup = {
        domain: itg
        for domain, itg in integrations_to_process.items()
        if domain in domains_to_setup
    }
    all_integrations_to_setup = integrations_to_setup.copy()
    all_integrations_to_setup.update(
        (dep, loader.async_get_loaded_integration(hass, dep))
        for domain in integrations_to_setup
        for dep in integrations_dependencies[domain].difference(
            all_integrations_to_setup
        )
    )

    # Gather requirements for all integrations,
    # their dependencies and after dependencies.
    # To gather all the requirements we must ignore exceptions here.
    # The exceptions will be detected and handled later in the bootstrap process.
    integrations_after_dependencies = (
        await loader.resolve_integrations_after_dependencies(
            hass, integrations_to_process.values(), ignore_exceptions=True
        )
    )
    integrations_requirements = {
        domain: itg.requirements for domain, itg in integrations_to_process.items()
    }
    integrations_requirements.update(
        (dep, loader.async_get_loaded_integration(hass, dep).requirements)
        for deps in integrations_after_dependencies.values()
        for dep in deps.difference(integrations_requirements)
    )
    all_requirements = set(chain.from_iterable(integrations_requirements.values()))

    # Optimistically check if requirements are already installed
    # ahead of setting up the integrations so we can prime the cache
    # We do not wait for this since it's an optimization only
    hass.async_create_background_task(
        requirements.async_load_installed_versions(hass, all_requirements),
        "check installed requirements",
        eager_start=True,
    )

    # Start loading translations for all integrations we are going to set up
    # in the background so they are ready when we need them. This avoids a
    # lot of waiting for the translation load lock and a thundering herd of
    # tasks trying to load the same translations at the same time as each
    # integration is loaded.
    #
    # We do not wait for this since as soon as the task runs it will
    # hold the translation load lock and if anything is fast enough to
    # wait for the translation load lock, loading will be done by the
    # time it gets to it.
    translations_to_load = {*all_integrations_to_setup, *additional_domains_to_process}
    hass.async_create_background_task(
        translation.async_load_integrations(hass, translations_to_load),
        "load translations",
        eager_start=True,
    )

    # Preload storage for all integrations we are going to set up
    # so we do not have to wait for it to be loaded when we need it
    # in the setup process.
    hass.async_create_background_task(
        get_internal_store_manager(hass).async_preload(
            [*PRELOAD_STORAGE, *all_integrations_to_setup]
        ),
        "preload storage",
        eager_start=True,
    )

    return integrations_to_setup, all_integrations_to_setup