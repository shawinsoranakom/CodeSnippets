def _populate_brand_integrations(
    integration_data: dict[str, Any],
    integrations: dict[str, Integration],
    brand_metadata: dict[str, Any],
    sub_integrations: list[str],
) -> None:
    """Add referenced integrations to a brand's metadata."""
    brand_metadata.setdefault("integrations", {})
    for domain in sub_integrations:
        integration = integrations.get(domain)
        if not integration or integration.integration_type in (
            IntegrationType.ENTITY,
            IntegrationType.SYSTEM,
        ):
            continue
        metadata: dict[str, Any] = {
            "integration_type": integration.integration_type,
        }
        # Always set the config_flow key to avoid breaking the frontend
        # https://github.com/home-assistant/frontend/issues/14376
        metadata["config_flow"] = bool(integration.config_flow)
        if integration.iot_class:
            metadata["iot_class"] = integration.iot_class
        if integration.supported_by:
            metadata["supported_by"] = integration.supported_by
        if integration.iot_standards:
            metadata["iot_standards"] = integration.iot_standards
        if integration.translated_name:
            integration_data["translated_name"].add(domain)
        else:
            metadata["name"] = integration.name
        brand_metadata["integrations"][domain] = metadata