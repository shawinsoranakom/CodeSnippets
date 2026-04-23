async def test_no_base_platforms_loaded_before_recorder(hass: HomeAssistant) -> None:
    """Verify stage 0 not load base platforms before recorder.

    If a stage 0 integration implements base platforms or has a base
    platform in its dependencies and it loads before the recorder,
    because of platform-based YAML schema, it may inadvertently
    load integrations that expect the recorder to already be loaded.
    We need to ensure that doesn't happen.
    """
    IGNORE_BASE_PLATFORM_FILES = {
        # config/scene.py is not a platform
        "config": {"scene.py"},
        # websocket_api/sensor.py is using the platform YAML schema
        # we must not migrate it to an integration key until
        # we remove the platform YAML schema support for sensors
        "websocket_api": {"sensor.py"},
    }
    # person is a special case because it is a base platform
    # in the sense that it creates entities in its namespace
    # but its not used by other integrations to create entities
    # so we want to make sure it is not loaded before the recorder
    base_platforms = BASE_PLATFORMS | {"person"}

    integrations_before_recorder: set[str] = set()
    for _, integrations, _ in bootstrap.STAGE_0_INTEGRATIONS:
        integrations_before_recorder |= integrations
        if "recorder" in integrations:
            break
    else:
        pytest.fail("recorder not in stage 0")

    integrations_or_excs = await loader.async_get_integrations(
        hass, integrations_before_recorder
    )
    integrations: dict[str, Integration] = {}
    for domain, integration in integrations_or_excs.items():
        assert not isinstance(integrations_or_excs, Exception)
        integrations[domain] = integration

    integrations_all_dependencies = (
        await loader.resolve_integrations_after_dependencies(
            hass, integrations.values(), ignore_exceptions=True
        )
    )
    all_integrations = integrations.copy()
    all_integrations.update(
        (domain, loader.async_get_loaded_integration(hass, domain))
        for domains in integrations_all_dependencies.values()
        for domain in domains
    )

    problems: dict[str, set[str]] = {}
    for domain in integrations:
        domain_with_base_platforms_deps = (
            integrations_all_dependencies[domain] & base_platforms
        )
        if domain_with_base_platforms_deps:
            problems[domain] = domain_with_base_platforms_deps
    assert not problems, (
        f"Integrations that are setup before recorder have base platforms in their dependencies: {problems}"
    )

    base_platform_py_files = {f"{base_platform}.py" for base_platform in base_platforms}

    for domain, integration in all_integrations.items():
        integration_base_platforms_files = (
            integration._top_level_files & base_platform_py_files
        )
        if ignore := IGNORE_BASE_PLATFORM_FILES.get(domain):
            integration_base_platforms_files -= ignore
        if integration_base_platforms_files:
            problems[domain] = integration_base_platforms_files
    assert not problems, (
        f"Integrations that are setup before recorder implement base platforms: {problems}"
    )