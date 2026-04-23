def _format_flow_outputs(self, graph: Graph) -> list[Output]:
        """Generate Output objects from the graph's outputs.

        The Output objects modify the name and method of the graph's outputs.
        The name is modified by prepending the vertex_id and to the original name,
        which uniquely identifies the output.
        The method is set to a dynamically generated method which uses a unique name
        to resolve the output to its value generated during the flow execution.

        Args:
            graph: The graph to generate outputs for.

        Returns:
            A list of Output objects.
        """
        output_vertices: list[Vertex] = [v for v in graph.vertices if v.is_output]
        outputs: list[Output] = []
        vdisp_cts = Counter(v.display_name for v in output_vertices)
        for vertex in output_vertices:
            if graph.successor_map.get(vertex.id, []):
                # skip output node if it has outgoing edges
                continue
            one_out = len(vertex.outputs) == 1
            for vertex_output in vertex.outputs:
                new_name = self._get_ioput_name(vertex.id, vertex_output.get("name"))
                output = Output(**vertex_output)
                output.name = new_name
                output.method = self._register_flow_output_method(
                    vertex_id=vertex.id,
                    output_name=vertex_output.get("name"),
                )
                vdn = vertex.display_name
                odn = output.display_name
                output.display_name = (
                    vdn
                    if one_out and vdisp_cts[vdn] == 1
                    else odn
                    + (
                        # output.display_name potentially collides w/ those of other vertices
                        f" ({vdn})"
                        if vdisp_cts[vdn] == 1
                        # output.display_name collides w/ those of duplicate vertices
                        else f"-{vertex.id}"
                    )
                )
                outputs.append(output)

        return outputs