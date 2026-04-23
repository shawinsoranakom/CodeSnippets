def check_input_mutation_on_current_stream(
        self, tx: "InstructionTranslatorBase"
    ) -> None:
        """Record which stream index has input mutations by comparing current
        tensor versions against the versions captured at graph input creation."""
        if not hasattr(tx, "symbolic_stream_state"):
            return
        if not tx.symbolic_stream_state.in_stream_context():
            return

        tracer = self.root_tracer
        if self._last_checked_input_versions is None:
            self._last_checked_input_versions = dict(
                enumerate(tracer._input_versions_at_beginning)
            )

        cur_stream_index = tx.symbolic_stream_state.cur_stream_id()
        input_idx = 0
        for node in tracer.graph.nodes:
            if node.op != "placeholder":
                break
            example_value = node.meta.get("example_value")
            if not isinstance(example_value, torch.Tensor):
                continue
            prev_version = self._last_checked_input_versions.get(input_idx)
            cur_version = example_value._version
            if prev_version is not None and cur_version > prev_version:
                if cur_stream_index not in self._input_mutation_streams:
                    self._input_mutation_streams[cur_stream_index] = (
                        TracingContext.extract_stack()
                    )
                self._last_checked_input_versions[input_idx] = cur_version
            input_idx += 1