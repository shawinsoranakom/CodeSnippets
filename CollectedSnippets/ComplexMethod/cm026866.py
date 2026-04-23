def _check_for_states_in_uom(
    isy_data: IsyData,
    node: Group | Node,
    single_platform: Platform | None = None,
    states_list: list[str] | None = None,
) -> bool:
    """Check if a list of uoms matches two possible filters.

    This is for versions of the ISY firmware that report uoms as a list of all
    possible "human readable" states. This filter passes if all of the possible
    states fit inside the given filter.
    """
    if not hasattr(node, "uom") or node.uom in (None, ""):
        # Node doesn't have a uom (Scenes for example)
        return False

    # This only works for ISYv4 Firmware where uom is a list of states:
    if not isinstance(node.uom, list):
        return False

    node_uom = set(map(str.lower, node.uom))

    if states_list and single_platform:
        if node_uom == set(states_list):
            isy_data.nodes[single_platform].append(node)
            return True
        return False

    platforms = NODE_PLATFORMS if not single_platform else [single_platform]
    for platform in platforms:
        if node_uom == set(NODE_FILTERS[platform][FILTER_STATES]):
            isy_data.nodes[platform].append(node)
            return True

    return False