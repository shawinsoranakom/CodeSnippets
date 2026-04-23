def _get_permissible_entity_candidates(
    call: ServiceCall,
    entities: Mapping[str, Entity],
    entity_perms: Callable[[str, str], bool] | None,
    target_all_entities: bool,
    all_referenced: set[str] | None,
) -> list[Entity]:
    """Get entity candidates that the user is allowed to access."""
    if entity_perms is not None:
        # Check the permissions since entity_perms is set
        if target_all_entities:
            # If we target all entities, we will select all entities the user
            # is allowed to control.
            return [
                entity
                for entity_id, entity in entities.items()
                if entity_perms(entity_id, POLICY_CONTROL)
            ]

        assert all_referenced is not None
        # If they reference specific entities, we will check if they are all
        # allowed to be controlled.
        for entity_id in all_referenced:
            if not entity_perms(entity_id, POLICY_CONTROL):
                raise Unauthorized(
                    context=call.context,
                    entity_id=entity_id,
                    permission=POLICY_CONTROL,
                )

    elif target_all_entities:
        return list(entities.values())

    # We have already validated they have permissions to control all_referenced
    # entities so we do not need to check again.
    if TYPE_CHECKING:
        assert all_referenced is not None
    if (
        len(all_referenced) == 1
        and (single_entity := list(all_referenced)[0])
        and (entity := entities.get(single_entity)) is not None
    ):
        return [entity]

    return [entities[entity_id] for entity_id in all_referenced.intersection(entities)]