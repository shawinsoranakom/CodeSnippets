def _accumulate_upstream_token_usage(self) -> Usage | None:
        """Accumulate token usage from all upstream vertices.

        Walks all recursive predecessors via edges, deduplicates by vertex ID,
        and sums their token usage into a single total.
        """
        predecessors = self._get_all_upstream_vertices()
        total_input = 0
        total_output = 0
        has_data = False

        for predecessor in predecessors:
            if predecessor.result and predecessor.result.token_usage:
                usage = predecessor.result.token_usage
                total_input += usage.input_tokens or 0
                total_output += usage.output_tokens or 0
                has_data = True

        # Include own token usage if present
        if self.custom_component:
            own_usage = self.custom_component._token_usage  # noqa: SLF001
            if own_usage:
                total_input += own_usage.input_tokens or 0
                total_output += own_usage.output_tokens or 0
                has_data = True

        if not has_data:
            return None

        return Usage(
            input_tokens=total_input,
            output_tokens=total_output,
            total_tokens=total_input + total_output,
        )