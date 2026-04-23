async def create_subgraph(self, vertex_ids: set[str]) -> AsyncIterator[Graph]:
        """Create an isolated subgraph containing only specified vertices.

        This creates a new Graph instance with only the vertices and edges
        that connect the specified vertices. The subgraph shares the same
        flow_id and user_id but gets its own context copy.

        Must be used as an async context manager to ensure proper cleanup
        of any pending trace tasks when the subgraph execution completes.

        Args:
            vertex_ids: Set of vertex IDs to include in the subgraph

        Yields:
            A new Graph instance containing only the specified vertices

        Example:
            async with graph.create_subgraph(vertex_ids) as subgraph:
                subgraph.prepare()
                async for result in subgraph.async_start():
                    process(result)
        """
        # Filter nodes to only include specified vertex IDs
        subgraph_nodes = [n for n in self._vertices if n["id"] in vertex_ids]

        # Filter edges to only include those connecting vertices in the subgraph
        subgraph_edges = [e for e in self._edges if e["source"] in vertex_ids and e["target"] in vertex_ids]

        # Create new graph instance with copied context
        subgraph = Graph(
            flow_id=self.flow_id,
            flow_name=f"{self.flow_name}_subgraph" if self.flow_name else "subgraph",
            user_id=self.user_id,
            context=dict(self.context) if self.context else None,
        )

        # Inherit parent's tracing context - subgraph is an extension of parent's execution
        subgraph._tracing_service = self._tracing_service
        subgraph._tracing_service_initialized = True
        subgraph._run_id = self._run_id
        subgraph.session_id = self.session_id
        subgraph._is_subgraph = True

        # Add the filtered nodes and edges
        subgraph.add_nodes_and_edges(subgraph_nodes, subgraph_edges)

        yield subgraph