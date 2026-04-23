def apply_replacements(self, prompt: dict[str, NodeStruct]):
        connections: dict[str, list[tuple[str, str, int]]] = {}
        need_replacement: set[str] = set()
        for node_number, node_struct in prompt.items():
            if "class_type" not in node_struct or "inputs" not in node_struct:
                continue
            class_type = node_struct["class_type"]
            # need replacement if not in NODE_CLASS_MAPPINGS and has replacement
            if class_type not in nodes.NODE_CLASS_MAPPINGS.keys() and self.has_replacement(class_type):
                need_replacement.add(node_number)
            # keep track of connections
            for input_id, input_value in node_struct["inputs"].items():
                if is_link(input_value):
                    conn_number = input_value[0]
                    connections.setdefault(conn_number, []).append((node_number, input_id, input_value[1]))
        for node_number in need_replacement:
            node_struct = prompt[node_number]
            class_type = node_struct["class_type"]
            replacements = self.get_replacement(class_type)
            if replacements is None:
                continue
            # just use the first replacement
            replacement = replacements[0]
            new_node_id = replacement.new_node_id
            # if replacement is not a valid node, skip trying to replace it as will only cause confusion
            if new_node_id not in nodes.NODE_CLASS_MAPPINGS.keys():
                continue
            # first, replace node id (class_type)
            new_node_struct = copy_node_struct(node_struct, empty_inputs=True)
            new_node_struct["class_type"] = new_node_id
            # TODO: consider replacing display_name in _meta as well for error reporting purposes; would need to query node schema
            # second, replace inputs
            if replacement.input_mapping is not None:
                for input_map in replacement.input_mapping:
                    if "set_value" in input_map:
                        new_node_struct["inputs"][input_map["new_id"]] = input_map["set_value"]
                    elif "old_id" in input_map:
                        new_node_struct["inputs"][input_map["new_id"]] = node_struct["inputs"][input_map["old_id"]]
            # finalize input replacement
            prompt[node_number] = new_node_struct
            # third, replace outputs
            if replacement.output_mapping is not None:
                # re-mapping outputs requires changing the input values of nodes that receive connections from this one
                if node_number in connections:
                    for conns in connections[node_number]:
                        conn_node_number, conn_input_id, old_output_idx = conns
                        for output_map in replacement.output_mapping:
                            if output_map["old_idx"] == old_output_idx:
                                new_output_idx = output_map["new_idx"]
                                previous_input = prompt[conn_node_number]["inputs"][conn_input_id]
                                previous_input[1] = new_output_idx