def _check_for_uom_id(
    isy_data: IsyData,
    node: Group | Node,
    single_platform: Platform | None = None,
    uom_list: list[str] | None = None,
) -> bool:
    """Check if a node's uom matches any of the platforms uom filter.

    This is used for versions of the ISY firmware that report uoms as a single
    ID. We can often infer what type of device it is by that ID.
    """
    if not hasattr(node, "uom") or node.uom in (None, ""):
        # Node doesn't have a uom (Scenes for example)
        return False

    # Backwards compatibility for ISYv4 Firmware:
    node_uom = node.uom
    if isinstance(node.uom, list):
        node_uom = node.uom[0]

    if uom_list and single_platform:
        if node_uom in uom_list:
            isy_data.nodes[single_platform].append(node)
            return True
        return False

    platforms = NODE_PLATFORMS if not single_platform else [single_platform]
    for platform in platforms:
        if node_uom in NODE_FILTERS[platform][FILTER_UOM]:
            isy_data.nodes[platform].append(node)
            return True

    return False