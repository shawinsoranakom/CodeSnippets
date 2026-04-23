def create_mapping_pre_post_grad_nodes(
    pre_grad_graph_id: int | None,
    post_to_pre_grad_nodes_json: dict[str, Any],
) -> dict[str, dict[str, list[str]]]:
    """
    Create bidirectional mappings between pre_grad graph nodes
    and post_grad graph code nodes, and vice versa.
    """
    # return a dummy dict if there's any error
    empty_return: dict[str, dict[str, list[str]]] = {
        "preToPost": {},
        "postToPre": {},
    }

    if not isinstance(post_to_pre_grad_nodes_json, dict):
        log.error("Provenance tacking error: post_to_pre_grad_nodes_json is not a dict")
        return empty_return

    if not isinstance(pre_grad_graph_id, int):
        # pre_grad_graph_id may be empty if there's no pre_grad graph
        # and there's only a backward graph from backward pass engine
        return empty_return

    pre_to_post: dict[str, Any] = collections.defaultdict(OrderedSet)
    post_to_pre: dict[str, Any] = collections.defaultdict(OrderedSet)

    try:

        def check_format(node: dict[str, Any]) -> bool:
            if not isinstance(node, dict):
                log.error(
                    "Provenance tacking error: node provenance in post_to_pre_grad_nodes_json is not a dict"
                )
                return False
            if "graph_id" not in node or "name" not in node or "from_node" not in node:
                log.error(
                    "Provenance tacking error: node provenance in post_to_pre_grad_nodes_json has wrong format"
                )
                return False
            return True

        for outer_key, node_array in post_to_pre_grad_nodes_json.items():
            if not isinstance(node_array, list):
                log.error(
                    "Provenance tacking error: post_to_pre_grad_nodes_json value is not a list"
                )
                return empty_return
            for node in node_array:
                if not check_format(node):
                    return empty_return
                # Check the current node first
                if node.get("graph_id") == pre_grad_graph_id:
                    pre_to_post[node["name"]].add(outer_key)
                    post_to_pre[outer_key].add(node["name"])

                # Check nested from_node array recursively, add node with the right graph_id to the map
                stack = [(n, outer_key) for n in node.get("from_node", [])]
                while stack:
                    current_node, parent_key = stack.pop()
                    if not check_format(current_node):
                        return empty_return
                    if current_node.get("graph_id") == pre_grad_graph_id:
                        pre_to_post[current_node["name"]].add(parent_key)
                        post_to_pre[parent_key].add(current_node["name"])
                    stack.extend(
                        (n, parent_key) for n in current_node.get("from_node", [])
                    )

        def convert_sets_to_lists(d: dict[str, Any]) -> None:
            for key in d:
                d[key] = list(d[key])
            d = dict(d)

        # convert to list because set is not JSON serializable
        convert_sets_to_lists(pre_to_post)
        convert_sets_to_lists(post_to_pre)
        return {
            "preToPost": pre_to_post,
            "postToPre": post_to_pre,
        }
    except Exception as e:
        # Since this is just logging code, it should never interfere with regular
        # program execution, so we use this try-except to guard against any error
        signpost_event(
            "inductor",
            "provenance_tracking_error",
            {
                "function": "create_mapping_pre_post_grad_nodes",
                "error_msg": str(e),
                "stack_trace": traceback.format_exc(),
            },
        )
        log.error("post_to_pre_grad_nodes_json:  %s", post_to_pre_grad_nodes_json)
        log.error("pre_grad_graph_id:  %s", pre_grad_graph_id)
        return empty_return