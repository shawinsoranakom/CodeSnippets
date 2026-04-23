def boruvka(self) -> None:
        """Performs Borůvka's algorithm to find MST."""

        # Initialize additional lists required to algorithm.
        component_size = []
        mst_weight = 0

        minimum_weight_edge: list[Any] = [-1] * self.m_num_of_nodes

        # A list of components (initialized to all of the nodes)
        for node in range(self.m_num_of_nodes):
            self.m_component.update({node: node})
            component_size.append(1)

        num_of_components = self.m_num_of_nodes

        while num_of_components > 1:
            for edge in self.m_edges:
                u, v, w = edge

                u_component = self.m_component[u]
                v_component = self.m_component[v]

                if u_component != v_component:
                    """If the current minimum weight edge of component u doesn't
                    exist (is -1), or if it's greater than the edge we're
                    observing right now, we will assign the value of the edge
                    we're observing to it.

                    If the current minimum weight edge of component v doesn't
                    exist (is -1), or if it's greater than the edge we're
                    observing right now, we will assign the value of the edge
                    we're observing to it"""

                    for component in (u_component, v_component):
                        if (
                            minimum_weight_edge[component] == -1
                            or minimum_weight_edge[component][2] > w
                        ):
                            minimum_weight_edge[component] = [u, v, w]

            for edge in minimum_weight_edge:
                if isinstance(edge, list):
                    u, v, w = edge

                    u_component = self.m_component[u]
                    v_component = self.m_component[v]

                    if u_component != v_component:
                        mst_weight += w
                        self.union(component_size, u_component, v_component)
                        print(f"Added edge [{u} - {v}]\nAdded weight: {w}\n")
                        num_of_components -= 1

            minimum_weight_edge = [-1] * self.m_num_of_nodes
        print(f"The total weight of the minimal spanning tree is: {mst_weight}")