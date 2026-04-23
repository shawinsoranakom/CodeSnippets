def while_loop_close(self, flow_control, condition, dynprompt=None, unique_id=None, **kwargs):
        assert dynprompt is not None
        if not condition:
            # We're done with the loop
            values = []
            for i in range(NUM_FLOW_SOCKETS):
                values.append(kwargs.get(f"initial_value{i}", None))
            return tuple(values)

        # We want to loop
        upstream = {}
        # Get the list of all nodes between the open and close nodes
        self.explore_dependencies(unique_id, dynprompt, upstream)

        contained = {}
        open_node = flow_control[0]
        self.collect_contained(open_node, upstream, contained)
        contained[unique_id] = True
        contained[open_node] = True

        # We'll use the default prefix, but to avoid having node names grow exponentially in size,
        # we'll use "Recurse" for the name of the recursively-generated copy of this node.
        graph = GraphBuilder()
        for node_id in contained:
            original_node = dynprompt.get_node(node_id)
            node = graph.node(original_node["class_type"], "Recurse" if node_id == unique_id else node_id)
            node.set_override_display_id(node_id)
        for node_id in contained:
            original_node = dynprompt.get_node(node_id)
            node = graph.lookup_node("Recurse" if node_id == unique_id else node_id)
            assert node is not None
            for k, v in original_node["inputs"].items():
                if is_link(v) and v[0] in contained:
                    parent = graph.lookup_node(v[0])
                    assert parent is not None
                    node.set_input(k, parent.out(v[1]))
                else:
                    node.set_input(k, v)
        new_open = graph.lookup_node(open_node)
        assert new_open is not None
        for i in range(NUM_FLOW_SOCKETS):
            key = f"initial_value{i}"
            new_open.set_input(key, kwargs.get(key, None))
        my_clone = graph.lookup_node("Recurse")
        assert my_clone is not None
        result = map(lambda x: my_clone.out(x), range(NUM_FLOW_SOCKETS))
        return {
            "result": tuple(result),
            "expand": graph.finalize(),
        }