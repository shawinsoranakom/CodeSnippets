async def async_install(entity: UpdateEntity, service_call: ServiceCall) -> None:
    """Service call wrapper to validate the call."""
    # If version is not specified, but no update is available.
    if (version := service_call.data.get(ATTR_VERSION)) is None and (
        entity.installed_version == entity.latest_version
        or entity.latest_version is None
    ):
        raise HomeAssistantError(f"No update available for {entity.entity_id}")

    # If version is specified, but not supported by the entity.
    if (
        version is not None
        and UpdateEntityFeature.SPECIFIC_VERSION not in entity.supported_features
    ):
        raise HomeAssistantError(
            f"Installing a specific version is not supported for {entity.entity_id}"
        )

    # If backup is requested, but not supported by the entity.
    if (
        backup := service_call.data[ATTR_BACKUP]
    ) and UpdateEntityFeature.BACKUP not in entity.supported_features:
        raise HomeAssistantError(f"Backup is not supported for {entity.entity_id}")

    # Update is already in progress.
    if entity.in_progress is not False:
        raise HomeAssistantError(
            f"Update installation already in progress for {entity.entity_id}"
        )

    await entity.async_install_with_progress(version, backup)