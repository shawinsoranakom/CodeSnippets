def update_new_output(data):
    nodes = copy.deepcopy(data["nodes"])
    edges = copy.deepcopy(data["edges"])

    for edge in edges:
        if "sourceHandle" in edge and "targetHandle" in edge:
            new_source_handle = scape_json_parse(edge["sourceHandle"])
            new_target_handle = scape_json_parse(edge["targetHandle"])
            id_ = new_source_handle["id"]
            source_node_index = next((index for (index, d) in enumerate(nodes) if d["id"] == id_), -1)
            source_node = nodes[source_node_index] if source_node_index != -1 else None

            if "baseClasses" in new_source_handle:
                if "output_types" not in new_source_handle:
                    if source_node and "node" in source_node["data"] and "output_types" in source_node["data"]["node"]:
                        new_source_handle["output_types"] = source_node["data"]["node"]["output_types"]
                    else:
                        new_source_handle["output_types"] = new_source_handle["baseClasses"]
                del new_source_handle["baseClasses"]

            if new_target_handle.get("inputTypes"):
                intersection = [
                    type_ for type_ in new_source_handle["output_types"] if type_ in new_target_handle["inputTypes"]
                ]
            else:
                intersection = [
                    type_ for type_ in new_source_handle["output_types"] if type_ == new_target_handle["type"]
                ]

            selected = intersection[0] if intersection else None
            if "name" not in new_source_handle:
                new_source_handle["name"] = " | ".join(new_source_handle["output_types"])
            new_source_handle["output_types"] = [selected] if selected else []

            if source_node and not source_node["data"]["node"].get("outputs"):
                if "outputs" not in source_node["data"]["node"]:
                    source_node["data"]["node"]["outputs"] = []
                types = source_node["data"]["node"].get(
                    "output_types", source_node["data"]["node"].get("base_classes", [])
                )
                if not any(output.get("selected") == selected for output in source_node["data"]["node"]["outputs"]):
                    source_node["data"]["node"]["outputs"].append(
                        {
                            "types": types,
                            "selected": selected,
                            "name": " | ".join(types),
                            "display_name": " | ".join(types),
                        }
                    )
            deduplicated_outputs = []
            if source_node is None:
                source_node = {"data": {"node": {"outputs": []}}}

            for output in source_node["data"]["node"]["outputs"]:
                if output["name"] not in [d["name"] for d in deduplicated_outputs]:
                    deduplicated_outputs.append(output)
            source_node["data"]["node"]["outputs"] = deduplicated_outputs

            edge["sourceHandle"] = escape_json_dump(new_source_handle)
            edge["data"]["sourceHandle"] = new_source_handle
            edge["data"]["targetHandle"] = new_target_handle
    # The above sets the edges but some of the sourceHandles do not have valid name
    # which can be found in the nodes. We need to update the sourceHandle with the
    # name from node['data']['node']['outputs']
    for node in nodes:
        if "outputs" in node["data"]["node"]:
            for output in node["data"]["node"]["outputs"]:
                for edge in edges:
                    if node["id"] != edge["source"] or output.get("method") is None:
                        continue
                    source_handle = scape_json_parse(edge["sourceHandle"])
                    if source_handle["output_types"] == output.get("types") and source_handle["name"] != output["name"]:
                        source_handle["name"] = output["name"]
                        if isinstance(source_handle, str):
                            source_handle = scape_json_parse(source_handle)
                        edge["sourceHandle"] = escape_json_dump(source_handle)
                        edge["data"]["sourceHandle"] = source_handle

    data_copy = copy.deepcopy(data)
    data_copy["nodes"] = nodes
    data_copy["edges"] = edges
    return data_copy