def process_tweaks(
    graph_data: dict[str, Any], tweaks: Tweaks | dict[str, dict[str, Any]], *, stream: bool = False
) -> dict[str, Any]:
    """This function is used to tweak the graph data using the node id and the tweaks dict.

    :param graph_data: The dictionary containing the graph data. It must contain a 'data' key with
                       'nodes' as its child or directly contain 'nodes' key. Each node should have an 'id' and 'data'.
    :param tweaks: The dictionary containing the tweaks. The keys can be the node id or the name of the tweak.
                   The values can be a dictionary containing the tweaks for the node or the value of the tweak.
    :param stream: A boolean flag indicating whether streaming should be deactivated across all components or not.
                   Default is False.
    :return: The modified graph_data dictionary.
    :raises ValueError: If the input is not in the expected format.
    """
    tweaks_dict = cast("dict[str, Any]", tweaks.model_dump()) if not isinstance(tweaks, dict) else tweaks
    if "stream" not in tweaks_dict:
        tweaks_dict |= {"stream": stream}
    nodes = validate_input(graph_data, cast("dict[str, str | dict[str, Any]]", tweaks_dict))
    nodes_map = {node.get("id"): node for node in nodes}
    nodes_display_name_map = {node.get("data", {}).get("node", {}).get("display_name"): node for node in nodes}

    all_nodes_tweaks = {}
    for key, value in tweaks_dict.items():
        if isinstance(value, dict):
            if (node := nodes_map.get(key)) or (node := nodes_display_name_map.get(key)):
                apply_tweaks(node, value)
        else:
            all_nodes_tweaks[key] = value
    if all_nodes_tweaks:
        for node in nodes:
            apply_tweaks(node, all_nodes_tweaks)

    return graph_data