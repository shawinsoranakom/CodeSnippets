async def _resolve_entity_service_call_entities(
    hass: HomeAssistant,
    registered_entities: Mapping[str, Entity] | Callable[[], Mapping[str, Entity]],
    call: ServiceCall,
    required_features: Iterable[int] | None = None,
    entity_device_classes: Iterable[str | None] | None = None,
) -> list[Entity] | None:
    """Resolve and filter entities for an entity service call."""
    entity_perms: Callable[[str, str], bool] | None = None

    if call.context.user_id:
        user = await hass.auth.async_get_user(call.context.user_id)
        if user is None:
            raise UnknownUser(context=call.context)
        if not user.is_admin:
            entity_perms = user.permissions.check_entity

    target_all_entities = call.data.get(ATTR_ENTITY_ID) == ENTITY_MATCH_ALL

    if target_all_entities:
        referenced: target_helpers.SelectedEntities | None = None
        all_referenced: set[str] | None = None
    else:
        # A set of entities we're trying to target.
        target_selection = target_helpers.TargetSelection(call.data)
        referenced = target_helpers.async_extract_referenced_entity_ids(
            hass, target_selection, True
        )
        all_referenced = referenced.referenced | referenced.indirectly_referenced

    if callable(registered_entities):
        _registered_entities = registered_entities()
    else:
        _registered_entities = registered_entities

    # A list with entities to call the service on.
    entity_candidates = _get_permissible_entity_candidates(
        call,
        _registered_entities,
        entity_perms,
        target_all_entities,
        all_referenced,
    )

    entity_candidates = [e for e in entity_candidates if e.available]

    if not target_all_entities:
        assert referenced is not None
        # Only report on explicit referenced entities
        missing = referenced.referenced.copy()
        for entity in entity_candidates:
            missing.discard(entity.entity_id)
        referenced.log_missing(missing, _LOGGER)

    entities: list[Entity] = []
    for entity in entity_candidates:
        # Skip entities that don't have the required device class.
        if (
            entity_device_classes is not None
            and entity.device_class not in entity_device_classes
        ):
            # If entity explicitly referenced, raise an error
            if referenced is not None and entity.entity_id in referenced.referenced:
                raise ServiceNotSupported(call.domain, call.service, entity.entity_id)

            continue

        # Skip entities that don't have the required feature.
        if required_features is not None and (
            entity.supported_features is None
            or not any(
                entity.supported_features & feature_set == feature_set
                for feature_set in required_features
            )
        ):
            # If entity explicitly referenced, raise an error
            if referenced is not None and entity.entity_id in referenced.referenced:
                raise ServiceNotSupported(call.domain, call.service, entity.entity_id)

            continue

        entities.append(entity)

    if not entities:
        if call.return_response:
            raise HomeAssistantError(
                "Service call requested response data but did not match any entities"
            )
        return None

    return entities