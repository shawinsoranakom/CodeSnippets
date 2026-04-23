def async_match_targets(  # noqa: C901
    hass: HomeAssistant,
    constraints: MatchTargetsConstraints,
    preferences: MatchTargetsPreferences | None = None,
    states: list[State] | None = None,
    area_candidate_filter: Callable[
        [MatchTargetsCandidate, Collection[str]], bool
    ] = _default_area_candidate_filter,
) -> MatchTargetsResult:
    """Match entities based on constraints in order to handle an intent."""
    preferences = preferences or MatchTargetsPreferences()
    filtered_by_domain = False

    if not states:
        # Get all states and filter by domain
        states = hass.states.async_all(constraints.domains)
        filtered_by_domain = True
        if not states:
            return MatchTargetsResult(False, MatchFailedReason.DOMAIN)

    candidates = [
        MatchTargetsCandidate(
            state=state,
            is_exposed=(
                async_should_expose(hass, constraints.assistant, state.entity_id)
                if constraints.assistant
                else True
            ),
        )
        for state in states
    ]

    if constraints.domains and (not filtered_by_domain):
        # Filter by domain (if we didn't already do it)
        candidates = [c for c in candidates if c.state.domain in constraints.domains]
        if not candidates:
            return MatchTargetsResult(False, MatchFailedReason.DOMAIN)

    if constraints.states:
        # Filter by state
        candidates = [c for c in candidates if c.state.state in constraints.states]
        if not candidates:
            return MatchTargetsResult(False, MatchFailedReason.STATE)

    # Try to exit early so we can avoid registry lookups
    if not (
        constraints.name
        or constraints.features
        or constraints.device_classes
        or constraints.area_name
        or constraints.floor_name
        or constraints.single_target
    ):
        if constraints.assistant:
            # Check exposure
            candidates = [c for c in candidates if c.is_exposed]
            if not candidates:
                return MatchTargetsResult(False, MatchFailedReason.ASSISTANT)

        return MatchTargetsResult(True, states=[c.state for c in candidates])

    # We need entity registry entries now
    ent_reg = er.async_get(hass)
    for candidate in candidates:
        candidate.entity = ent_reg.async_get(candidate.state.entity_id)

    if constraints.name:
        # Filter by entity name or alias
        candidates = list(_filter_by_name(hass, constraints.name, candidates))
        if not candidates:
            return MatchTargetsResult(False, MatchFailedReason.NAME)

    if constraints.features:
        # Filter by supported features
        candidates = list(_filter_by_features(constraints.features, candidates))
        if not candidates:
            return MatchTargetsResult(False, MatchFailedReason.FEATURE)

    if constraints.device_classes:
        # Filter by device class
        candidates = list(
            _filter_by_device_classes(constraints.device_classes, candidates)
        )
        if not candidates:
            return MatchTargetsResult(False, MatchFailedReason.DEVICE_CLASS)

    # Check floor/area constraints
    targeted_floors: list[fr.FloorEntry] | None = None
    targeted_areas: list[ar.AreaEntry] | None = None

    # True when area information has been added to candidates
    areas_added = False

    if constraints.floor_name or constraints.area_name:
        area_reg = ar.async_get(hass)
        dev_reg = dr.async_get(hass)
        _add_areas(area_reg, dev_reg, candidates)
        areas_added = True

        if constraints.floor_name:
            # Filter by areas associated with floor
            floor_reg = fr.async_get(hass)
            targeted_floors = list(find_floors(constraints.floor_name, floor_reg))
            if not targeted_floors:
                return MatchTargetsResult(
                    False,
                    MatchFailedReason.INVALID_FLOOR,
                    no_match_name=constraints.floor_name,
                )

            possible_floor_ids = {floor.floor_id for floor in targeted_floors}
            possible_area_ids = {
                area.id
                for area in area_reg.async_list_areas()
                if area.floor_id in possible_floor_ids
            }

            candidates = [
                c for c in candidates if area_candidate_filter(c, possible_area_ids)
            ]
            if not candidates:
                return MatchTargetsResult(
                    False, MatchFailedReason.FLOOR, floors=targeted_floors
                )
        else:
            # All areas are possible
            possible_area_ids = {area.id for area in area_reg.async_list_areas()}

        if constraints.area_name:
            targeted_areas = list(find_areas(constraints.area_name, area_reg))
            if not targeted_areas:
                return MatchTargetsResult(
                    False,
                    MatchFailedReason.INVALID_AREA,
                    no_match_name=constraints.area_name,
                )

            matching_area_ids = {area.id for area in targeted_areas}

            # May be constrained by floors above
            possible_area_ids.intersection_update(matching_area_ids)
            candidates = [
                c for c in candidates if area_candidate_filter(c, possible_area_ids)
            ]
            if not candidates:
                return MatchTargetsResult(
                    False, MatchFailedReason.AREA, areas=targeted_areas
                )

    if constraints.assistant:
        # Check exposure
        candidates = [c for c in candidates if c.is_exposed]
        if not candidates:
            return MatchTargetsResult(False, MatchFailedReason.ASSISTANT)

    if constraints.name and (not constraints.allow_duplicate_names):
        # Check for duplicates
        if not areas_added:
            area_reg = ar.async_get(hass)
            dev_reg = dr.async_get(hass)
            _add_areas(area_reg, dev_reg, candidates)
            areas_added = True

        sorted_candidates = sorted(
            [c for c in candidates if c.matched_name],
            key=lambda c: c.matched_name or "",
        )
        final_candidates: list[MatchTargetsCandidate] = []
        for name, group in groupby(sorted_candidates, key=lambda c: c.matched_name):
            group_candidates = list(group)
            if len(group_candidates) < 2:
                # No duplicates for name
                final_candidates.extend(group_candidates)
                continue

            # Try to disambiguate by preferences
            if preferences.floor_id:
                group_candidates = [
                    c
                    for c in group_candidates
                    if (c.area is not None)
                    and (c.area.floor_id == preferences.floor_id)
                ]
                if len(group_candidates) < 2:
                    # Disambiguated by floor
                    final_candidates.extend(group_candidates)
                    continue

            if preferences.area_id:
                group_candidates = [
                    c
                    for c in group_candidates
                    if area_candidate_filter(c, {preferences.area_id})
                ]
                if len(group_candidates) < 2:
                    # Disambiguated by area
                    final_candidates.extend(group_candidates)
                    continue

            # Couldn't disambiguate duplicate names
            return MatchTargetsResult(
                False,
                MatchFailedReason.DUPLICATE_NAME,
                no_match_name=name,
                areas=targeted_areas or [],
                floors=targeted_floors or [],
            )

        if not final_candidates:
            return MatchTargetsResult(
                False,
                MatchFailedReason.NAME,
                areas=targeted_areas or [],
                floors=targeted_floors or [],
            )

        candidates = final_candidates

    if constraints.single_target and len(candidates) > 1:
        # Find best match using preferences
        if not (preferences.area_id or preferences.floor_id):
            # No preferences
            return MatchTargetsResult(
                False,
                MatchFailedReason.MULTIPLE_TARGETS,
                states=[c.state for c in candidates],
            )

        if not areas_added:
            area_reg = ar.async_get(hass)
            dev_reg = dr.async_get(hass)
            _add_areas(area_reg, dev_reg, candidates)
            areas_added = True

        filtered_candidates: list[MatchTargetsCandidate] = candidates
        if preferences.area_id:
            # Filter by area
            filtered_candidates = [
                c for c in candidates if area_candidate_filter(c, {preferences.area_id})
            ]

        if (len(filtered_candidates) > 1) and preferences.floor_id:
            # Filter by floor
            filtered_candidates = [
                c
                for c in candidates
                if c.area and (c.area.floor_id == preferences.floor_id)
            ]

        if len(filtered_candidates) != 1:
            # Filtering could not restrict to a single target
            return MatchTargetsResult(
                False,
                MatchFailedReason.MULTIPLE_TARGETS,
                states=[c.state for c in candidates],
            )

        # Filtering succeeded
        candidates = filtered_candidates

    return MatchTargetsResult(
        True,
        None,
        states=[c.state for c in candidates],
        areas=targeted_areas or [],
        floors=targeted_floors or [],
    )