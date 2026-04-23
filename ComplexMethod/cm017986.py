async def test_recorder_not_promoted(hass: HomeAssistant) -> None:
    """Verify that recorder is not promoted to earlier than its own stage."""
    integrations_before_recorder: set[str] = set()
    for _, integrations, _ in bootstrap.STAGE_0_INTEGRATIONS:
        if "recorder" in integrations:
            break
        integrations_before_recorder |= integrations
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

    assert "recorder" not in all_integrations