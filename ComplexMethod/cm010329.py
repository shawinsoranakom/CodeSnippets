def emit(self, record: Any) -> None:
        def _log_expression_created(
            emit_func: Callable[[Any], None], sym_node_id: int
        ) -> None:
            # Log all the relevant expression_created logs
            if sym_node_id is None:
                return
            if res := self.expression_created_logs.get(sym_node_id, None):
                # Don't log the expression if we have already
                # printed it beforehand
                if not res.visited:
                    res.visited = True
                    for arg in res.argument_ids:
                        _log_expression_created(emit_func, arg)

                emit_func(res.record)

        metadata = record.metadata
        for key in self.specific_log_keys:
            if key in metadata:
                if self.log_record.try_add((key, metadata[key])):
                    if key == "expression_created":
                        # We don't want to log all expression_created logs, only
                        # the ones that are relevant to the
                        # guards/propagate_real_tensor
                        self.expression_created_logs[metadata[key]["result_id"]] = (
                            ExpressionCreatedNode(
                                metadata[key]["result_id"],
                                metadata[key].get("argument_ids", []),
                                record,
                            )
                        )
                        return

                    elif key == "propagate_real_tensors_provenance":
                        _log_expression_created(
                            super().emit, metadata[key].get("expr_node_id")
                        )

                    elif key == "guard_added":
                        if len(metadata[key]["symbol_to_sources"]) == 0:
                            # We only want to include guards added that are relevant to
                            # the symbolic shapes corresponding to the inputs which were
                            # specified in the dynamic_shapes arg. These have a source.
                            return
                        elif metadata[key]["prefix"] == "runtime_assert":
                            # This should've been captured by a
                            # propagate_real_tensors log
                            return

                        _log_expression_created(
                            super().emit, metadata[key].get("expr_node_id")
                        )

                    super().emit(record)