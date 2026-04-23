def expand_entity_ids(hass: HomeAssistant, entity_ids: Iterable[Any]) -> list[str]:
    """Return entity_ids with group entity ids replaced by their members.

    Async friendly.
    """
    group_entities = get_group_entities(hass)

    found_ids: list[str] = []
    for entity_id in entity_ids:
        if not isinstance(entity_id, str) or entity_id in (
            ENTITY_MATCH_NONE,
            ENTITY_MATCH_ALL,
        ):
            continue

        entity_id = entity_id.lower()

        # If entity_id points at a group, expand it
        if (entity := group_entities.get(entity_id)) is not None and isinstance(
            entity.group, GenericGroup
        ):
            child_entities = entity.group.member_entity_ids
            if entity_id in child_entities:
                child_entities = list(child_entities)
                child_entities.remove(entity_id)
            found_ids.extend(
                ent_id
                for ent_id in expand_entity_ids(hass, child_entities)
                if ent_id not in found_ids
            )
        # If entity_id points at an old-style group, expand it
        elif entity_id.startswith(ENTITY_PREFIX):
            child_entities = get_entity_ids(hass, entity_id)
            if entity_id in child_entities:
                child_entities = list(child_entities)
                child_entities.remove(entity_id)
            found_ids.extend(
                ent_id
                for ent_id in expand_entity_ids(hass, child_entities)
                if ent_id not in found_ids
            )
        elif entity_id not in found_ids:
            found_ids.append(entity_id)

    return found_ids