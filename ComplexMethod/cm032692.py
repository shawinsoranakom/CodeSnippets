async def _merge_graph_nodes(self, graph: nx.Graph, nodes: list[str], change: GraphChange, task_id=""):
        if task_id and has_canceled(task_id):
            raise TaskCanceledException(f"Task {task_id} was cancelled during merge graph nodes")

        if len(nodes) <= 1:
            return
        change.added_updated_nodes.add(nodes[0])
        change.removed_nodes.update(nodes[1:])
        nodes_set = set(nodes)
        node0_attrs = graph.nodes[nodes[0]]
        node0_neighbors = set(graph.neighbors(nodes[0]))
        for node1 in nodes[1:]:
            if task_id and has_canceled(task_id):
                raise TaskCanceledException(f"Task {task_id} was cancelled during merge_graph nodes")

            # Merge two nodes, keep "entity_name", "entity_type", "page_rank" unchanged.
            node1_attrs = graph.nodes[node1]
            node0_attrs["description"] += f"{GRAPH_FIELD_SEP}{node1_attrs['description']}"
            node0_attrs["source_id"] = sorted(set(node0_attrs["source_id"] + node1_attrs["source_id"]))
            for neighbor in graph.neighbors(node1):
                change.removed_edges.add(get_from_to(node1, neighbor))
                if neighbor not in nodes_set:
                    edge1_attrs = graph.get_edge_data(node1, neighbor)
                    if neighbor in node0_neighbors:
                        # Merge two edges
                        change.added_updated_edges.add(get_from_to(nodes[0], neighbor))
                        edge0_attrs = graph.get_edge_data(nodes[0], neighbor)
                        edge0_attrs["weight"] += edge1_attrs["weight"]
                        edge0_attrs["description"] += f"{GRAPH_FIELD_SEP}{edge1_attrs['description']}"
                        for attr in ["keywords", "source_id"]:
                            edge0_attrs[attr] = sorted(set(edge0_attrs[attr] + edge1_attrs[attr]))
                        edge0_attrs["description"] = await self._handle_entity_relation_summary(f"({nodes[0]}, {neighbor})", edge0_attrs["description"], task_id=task_id)
                        graph.add_edge(nodes[0], neighbor, **edge0_attrs)
                    else:
                        graph.add_edge(nodes[0], neighbor, **edge1_attrs)
            graph.remove_node(node1)
        node0_attrs["description"] = await self._handle_entity_relation_summary(nodes[0], node0_attrs["description"], task_id=task_id)
        graph.nodes[nodes[0]].update(node0_attrs)