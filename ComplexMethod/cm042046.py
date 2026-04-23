def dfs(idx: int, obs_node_id: str, depth: int) -> str:
        tree_str = ""
        node = accessibility_tree[idx]
        indent = "\t" * depth
        valid_node = True
        try:
            role = node["role"]["value"]
            name = node["name"]["value"]
            node_str = f"[{obs_node_id}] {role} {repr(name)}"
            properties = []
            for property in node.get("properties", []):
                try:
                    if property["name"] in IGNORED_ACTREE_PROPERTIES:
                        continue
                    properties.append(f'{property["name"]}: {property["value"]["value"]}')
                except KeyError:
                    pass

            if properties:
                node_str += " " + " ".join(properties)

            # check valid
            if not node_str.strip():
                valid_node = False

            # empty generic node
            if not name.strip():
                if not properties:
                    if role in [
                        "generic",
                        "img",
                        "list",
                        "strong",
                        "paragraph",
                        "banner",
                        "navigation",
                        "Section",
                        "LabelText",
                        "Legend",
                        "listitem",
                    ]:
                        valid_node = False
                elif role in ["listitem"]:
                    valid_node = False

            if valid_node:
                tree_str += f"{indent}{node_str}"
                obs_nodes_info[obs_node_id] = {
                    "backend_id": node["backendDOMNodeId"],
                    "union_bound": node["union_bound"],
                    "text": node_str,
                }

        except Exception:
            valid_node = False

        for _, child_node_id in enumerate(node["childIds"]):
            if child_node_id not in node_id_to_idx:
                continue
            # mark this to save some tokens
            child_depth = depth + 1 if valid_node else depth
            child_str = dfs(node_id_to_idx[child_node_id], child_node_id, child_depth)
            if child_str.strip():
                if tree_str.strip():
                    tree_str += "\n"
                tree_str += child_str

        return tree_str