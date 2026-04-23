def _get_unmatched_response(result: RecognizeResult) -> tuple[ErrorKey, dict[str, Any]]:
    """Get key and template arguments for error when there are unmatched intent entities/slots."""

    # Filter out non-text and missing context entities
    unmatched_text: dict[str, str] = {
        key: entity.text.strip()
        for key, entity in result.unmatched_entities.items()
        if isinstance(entity, UnmatchedTextEntity) and entity.text != MISSING_ENTITY
    }

    if unmatched_area := unmatched_text.get("area"):
        # area only
        return ErrorKey.NO_AREA, {"area": unmatched_area}

    if unmatched_floor := unmatched_text.get("floor"):
        # floor only
        return ErrorKey.NO_FLOOR, {"floor": unmatched_floor}

    # Area may still have matched
    matched_area: str | None = None
    if matched_area_entity := result.entities.get("area"):
        matched_area = matched_area_entity.text.strip()

    matched_floor: str | None = None
    if matched_floor_entity := result.entities.get("floor"):
        matched_floor = matched_floor_entity.text.strip()

    if unmatched_name := unmatched_text.get("name"):
        if matched_area:
            # device in area
            return ErrorKey.NO_ENTITY_IN_AREA, {
                "entity": unmatched_name,
                "area": matched_area,
            }
        if matched_floor:
            # device on floor
            return ErrorKey.NO_ENTITY_IN_FLOOR, {
                "entity": unmatched_name,
                "floor": matched_floor,
            }

        # device only
        return ErrorKey.NO_ENTITY, {"entity": unmatched_name}

    # Default error
    return ErrorKey.NO_INTENT, {}