def _generate_filter_from_sets_and_pattern_lists(
    include_d: set[str],
    include_e: set[str],
    exclude_d: set[str],
    exclude_e: set[str],
    include_eg: re.Pattern[str] | None,
    exclude_eg: re.Pattern[str] | None,
) -> Callable[[str], bool]:
    """Generate a filter from pre-comuted sets and pattern lists."""
    have_exclude = bool(exclude_e or exclude_d or exclude_eg)
    have_include = bool(include_e or include_d or include_eg)

    # Case 1 - No filter
    # - All entities included
    if not have_include and not have_exclude:
        return bool

    # Case 2 - Only includes
    # - Entity listed in entities include: include
    # - Otherwise, entity matches domain include: include
    # - Otherwise, entity matches glob include: include
    # - Otherwise: exclude
    if have_include and not have_exclude:

        @lru_cache(maxsize=MAX_EXPECTED_ENTITY_IDS)
        def entity_included(entity_id: str) -> bool:
            """Return true if entity matches inclusion filters."""
            return (
                entity_id in include_e
                or split_entity_id(entity_id)[0] in include_d
                or (bool(include_eg and include_eg.match(entity_id)))
            )

        # Return filter function for case 2
        return entity_included

    # Case 3 - Only excludes
    # - Entity listed in exclude: exclude
    # - Otherwise, entity matches domain exclude: exclude
    # - Otherwise, entity matches glob exclude: exclude
    # - Otherwise: include
    if not have_include and have_exclude:

        @lru_cache(maxsize=MAX_EXPECTED_ENTITY_IDS)
        def entity_not_excluded(entity_id: str) -> bool:
            """Return true if entity matches exclusion filters."""
            return not (
                entity_id in exclude_e
                or split_entity_id(entity_id)[0] in exclude_d
                or (exclude_eg and exclude_eg.match(entity_id))
            )

        return entity_not_excluded

    # Case 4 - Domain and/or glob includes (may also have excludes)
    # - Entity listed in entities include: include
    # - Otherwise, entity listed in entities exclude: exclude
    # - Otherwise, entity matches glob include: include
    # - Otherwise, entity matches glob exclude: exclude
    # - Otherwise, entity matches domain include: include
    # - Otherwise: exclude
    if include_d or include_eg:

        @lru_cache(maxsize=MAX_EXPECTED_ENTITY_IDS)
        def entity_filter_4a(entity_id: str) -> bool:
            """Return filter function for case 4a."""
            return entity_id in include_e or (
                entity_id not in exclude_e
                and (
                    bool(include_eg and include_eg.match(entity_id))
                    or (
                        split_entity_id(entity_id)[0] in include_d
                        and not (exclude_eg and exclude_eg.match(entity_id))
                    )
                )
            )

        return entity_filter_4a

    # Case 5 - Domain and/or glob excludes (no domain and/or glob includes)
    # - Entity listed in entities include: include
    # - Otherwise, entity listed in exclude: exclude
    # - Otherwise, entity matches glob exclude: exclude
    # - Otherwise, entity matches domain exclude: exclude
    # - Otherwise: include
    if exclude_d or exclude_eg:

        @lru_cache(maxsize=MAX_EXPECTED_ENTITY_IDS)
        def entity_filter_4b(entity_id: str) -> bool:
            """Return filter function for case 4b."""
            domain = split_entity_id(entity_id)[0]
            if domain in exclude_d or bool(exclude_eg and exclude_eg.match(entity_id)):
                return entity_id in include_e
            return entity_id not in exclude_e

        return entity_filter_4b

    # Case 6 - No Domain and/or glob includes or excludes
    # - Entity listed in entities include: include
    # - Otherwise: exclude
    return partial(operator.contains, include_e)