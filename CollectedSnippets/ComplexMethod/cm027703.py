def _generate_integrations(
    brands: dict[str, Brand],
    integrations: dict[str, Integration],
    config: Config,
) -> str:
    """Generate integrations data."""

    result: dict[str, Any] = {
        "integration": {},
        "helper": {},
        "translated_name": set(),
    }

    # Not all integrations will have an item in the brands collection.
    # The config flow data index will be the union of the integrations without a brands item
    # and the brand domain names from the brands collection.

    # Compile a set of integrations which are referenced from at least one brand's
    # integrations list. These integrations will not be present in the root level of the
    # generated config flow index.
    brand_integration_domains = {
        brand_integration_domain
        for brand in brands.values()
        for brand_integration_domain in brand.integrations or []
    }

    # Compile a set of integrations which are not referenced from any brand's
    # integrations list.
    primary_domains = {
        domain
        for domain, integration in integrations.items()
        if domain not in brand_integration_domains
    }
    # Add all brands to the set
    primary_domains |= set(brands)

    # Generate the config flow index
    for domain in sorted(primary_domains):
        metadata: dict[str, Any] = {}

        if brand := brands.get(domain):
            metadata["name"] = brand.name
            if brand.integrations:
                # Add the integrations which are referenced from the brand's
                # integrations list
                _populate_brand_integrations(
                    result, integrations, metadata, brand.integrations
                )
            if brand.iot_standards:
                metadata["iot_standards"] = brand.iot_standards
            result["integration"][domain] = metadata
        else:  # integration
            integration = integrations[domain]
            if integration.integration_type in (
                IntegrationType.ENTITY,
                IntegrationType.SYSTEM,
            ):
                continue

            if integration.translated_name:
                result["translated_name"].add(domain)
            else:
                metadata["name"] = integration.name

            metadata["integration_type"] = integration.integration_type

            if integration.integration_type == IntegrationType.VIRTUAL:
                if integration.supported_by:
                    metadata["supported_by"] = integration.supported_by
                if integration.iot_standards:
                    metadata["iot_standards"] = integration.iot_standards
            else:
                metadata["config_flow"] = integration.config_flow
                if integration.iot_class:
                    metadata["iot_class"] = integration.iot_class

                if single_config_entry := integration.manifest.get(
                    "single_config_entry"
                ):
                    metadata["single_config_entry"] = single_config_entry

            if integration.integration_type == IntegrationType.HELPER:
                result["helper"][domain] = metadata
            else:
                result["integration"][domain] = metadata

    return json.dumps(
        result | {"translated_name": sorted(result["translated_name"])}, indent=2
    )