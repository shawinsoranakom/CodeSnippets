async def _resolve_flow_output(self, *, vertex_id: str, output_name: str):
        """Resolve the value of a given vertex's output.

            Given a vertex_id and output_name, it will resolve the value of the output
            belonging to the vertex with the given vertex_id.

        Args:
            vertex_id: The ID of the vertex to resolve the output for.
            output_name: The name of the output to resolve.

        Returns:
            The resolved output.
        """
        run_outputs = await self._get_cached_run_outputs(
            user_id=self.user_id,
            output_type="any",
        )
        if not run_outputs:
            return None

        first_output = run_outputs[0]
        if not first_output.outputs:
            return None
        for result in first_output.outputs:
            if not (result and result.component_id == vertex_id):
                continue
            if isinstance(result.results, dict) and output_name in result.results:
                return result.results[output_name]
            if result.artifacts and output_name in result.artifacts:
                return result.artifacts[output_name]
            return result.results or result.artifacts or result.outputs

        return None