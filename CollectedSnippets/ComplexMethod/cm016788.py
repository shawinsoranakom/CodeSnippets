def add_node(self, node_unique_id, include_lazy=False, subgraph_nodes=None):
        node_ids = [node_unique_id]
        links = []

        while len(node_ids) > 0:
            unique_id = node_ids.pop()
            if unique_id in self.pendingNodes:
                continue

            self.pendingNodes[unique_id] = True
            self.blockCount[unique_id] = 0
            self.blocking[unique_id] = {}

            inputs = self.dynprompt.get_node(unique_id)["inputs"]
            for input_name in inputs:
                value = inputs[input_name]
                if is_link(value):
                    from_node_id, from_socket = value
                    if subgraph_nodes is not None and from_node_id not in subgraph_nodes:
                        continue
                    _, _, input_info = self.get_input_info(unique_id, input_name)
                    is_lazy = input_info is not None and "lazy" in input_info and input_info["lazy"]
                    if (include_lazy or not is_lazy):
                        if not self.is_cached(from_node_id):
                            node_ids.append(from_node_id)
                        links.append((from_node_id, from_socket, unique_id))

        for link in links:
            self.add_strong_link(*link)