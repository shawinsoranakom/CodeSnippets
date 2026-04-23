async def async_get_all_descriptions(
    hass: HomeAssistant,
) -> dict[str, dict[str, Any]]:
    """Return descriptions (i.e. user documentation) for all service calls."""
    descriptions_cache = hass.data.setdefault(SERVICE_DESCRIPTION_CACHE, {})

    # We don't mutate services here so we avoid calling
    # async_services which makes a copy of every services
    # dict.
    services = hass.services.async_services_internal()

    # See if there are new services not seen before.
    # Any service that we saw before already has an entry in description_cache.
    all_services = {
        (domain, service_name)
        for domain, services_by_domain in services.items()
        for service_name in services_by_domain
    }
    # If we have a complete cache, check if it is still valid
    if all_cache := hass.data.get(ALL_SERVICE_DESCRIPTIONS_CACHE):
        previous_all_services, previous_descriptions_cache = all_cache
        # If the services are the same, we can return the cache
        if previous_all_services == all_services:
            return previous_descriptions_cache

    # Files we loaded for missing descriptions
    loaded: dict[str, JSON_TYPE] = {}
    # We try to avoid making a copy in the event the cache is good,
    # but now we must make a copy in case new services get added
    # while we are loading the missing ones so we do not
    # add the new ones to the cache without their descriptions
    services = {domain: service.copy() for domain, service in services.items()}

    if domains_with_missing_services := {
        domain for domain, _ in all_services.difference(descriptions_cache)
    }:
        ints_or_excs = await async_get_integrations(hass, domains_with_missing_services)
        integrations: list[Integration] = []
        for domain, int_or_exc in ints_or_excs.items():
            if type(int_or_exc) is Integration and int_or_exc.has_services:
                integrations.append(int_or_exc)
                continue
            if TYPE_CHECKING:
                assert isinstance(int_or_exc, Exception)
            _LOGGER.error(
                "Failed to load services.yaml for integration: %s",
                domain,
                exc_info=int_or_exc,
            )

        if integrations:
            loaded = await hass.async_add_executor_job(
                _load_services_files, integrations
            )

    # Build response
    descriptions: dict[str, dict[str, Any]] = {}
    for domain, services_map in services.items():
        descriptions[domain] = {}
        domain_descriptions = descriptions[domain]

        for service_name, service in services_map.items():
            cache_key = (domain, service_name)
            description = descriptions_cache.get(cache_key)
            if description is not None:
                domain_descriptions[service_name] = description
                continue

            # Cache missing descriptions
            domain_yaml = loaded.get(domain) or {}
            # The YAML may be empty for dynamically defined
            # services (e.g. shell_command) that never call
            # service.async_set_service_schema for the dynamic
            # service

            yaml_description = (
                domain_yaml.get(service_name) or {}  # type: ignore[union-attr]
            )

            # Don't warn for missing services, because it triggers false
            # positives for things like scripts, that register as a service
            description = {"fields": yaml_description.get("fields", {})}
            if description_placeholders := service.description_placeholders:
                description["description_placeholders"] = description_placeholders

            for item in ("description", "name", "target"):
                if item in yaml_description:
                    description[item] = yaml_description[item]

            response = service.supports_response
            if response is not SupportsResponse.NONE:
                description["response"] = {
                    "optional": response is SupportsResponse.OPTIONAL,
                }

            descriptions_cache[cache_key] = description

            domain_descriptions[service_name] = description

    hass.data[ALL_SERVICE_DESCRIPTIONS_CACHE] = (all_services, descriptions)
    return descriptions