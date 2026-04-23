async def async_get_integrations(
    hass: HomeAssistant, domains: Iterable[str]
) -> dict[str, Integration | Exception]:
    """Get integrations."""
    cache = hass.data[DATA_INTEGRATIONS]
    results: dict[str, Integration | Exception] = {}
    needed: dict[str, asyncio.Future[Integration | IntegrationNotFound]] = {}
    in_progress: dict[str, asyncio.Future[Integration | IntegrationNotFound]] = {}
    for domain in domains:
        int_or_fut = cache.get(domain)
        # Integration is never subclassed, so we can check for type
        if type(int_or_fut) is Integration:
            results[domain] = int_or_fut
        elif int_or_fut:
            if TYPE_CHECKING:
                assert isinstance(int_or_fut, asyncio.Future)
            in_progress[domain] = int_or_fut
        elif "." in domain:
            results[domain] = ValueError(f"Invalid domain {domain}")
        else:
            needed[domain] = cache[domain] = hass.loop.create_future()

    if in_progress:
        await asyncio.wait(in_progress.values())
        # Here we retrieve the results we waited for
        # instead of reading them from the cache since
        # reading from the cache will have a race if
        # the integration gets removed from the cache
        # because it was not found.
        for domain, future in in_progress.items():
            results[domain] = future.result()

    if not needed:
        return results

    # First we look for custom components
    # Instead of using resolve_from_root we use the cache of custom
    # components to find the integration.
    custom = await async_get_custom_components(hass)
    for domain, future in needed.items():
        if integration := custom.get(domain):
            results[domain] = cache[domain] = integration
            future.set_result(integration)

    for domain in results:
        if domain in needed:
            del needed[domain]

    # Now the rest use resolve_from_root
    if needed:
        from . import components  # noqa: PLC0415

        integrations = await hass.async_add_executor_job(
            _resolve_integrations_from_root, hass, components, needed
        )
        for domain, future in needed.items():
            if integration := integrations.get(domain):
                results[domain] = cache[domain] = integration
                future.set_result(integration)
            else:
                # We don't cache that it doesn't exist as configuration
                # validation that relies on integrations being loaded
                # would be unfixable. For example if a custom integration
                # was temporarily removed.
                # This allows restoring a missing integration to fix the
                # validation error so the config validations checks do not
                # block restarting.
                del cache[domain]
                exc = IntegrationNotFound(domain)
                results[domain] = exc
                # We don't use set_exception because
                # we expect there will be cases where
                # the future exception is never retrieved
                future.set_result(exc)

    return results