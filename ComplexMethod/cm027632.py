def _async_derive_object_ids(
    entity: Entity, platform: EntityPlatform, *, fallback_object_id: str | None = None
) -> tuple[str | None, str | None]:
    """Derive the object IDs for an entity.

    Derives both suggested and base object IDs.
    """
    is_base = True
    object_id: str | None

    if entity.internal_integration_suggested_object_id is not None:
        is_base = False
        object_id = entity.internal_integration_suggested_object_id
    else:
        object_id = entity.suggested_object_id

    if not object_id and fallback_object_id is not None:
        object_id = fallback_object_id

    if platform.entity_namespace is not None:
        is_base = False
        if entity.unique_id is not None and not object_id:
            object_id = f"{platform.platform_name}_{entity.unique_id}"
        object_id = f"{platform.entity_namespace} {object_id}"

    suggested_object_id: str | None = None
    object_id_base: str | None = None
    if is_base:
        object_id_base = object_id
    else:
        suggested_object_id = object_id

    return suggested_object_id, object_id_base