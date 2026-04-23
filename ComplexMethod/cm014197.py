def _call_function(
        self,
        tx: "InstructionTranslator",
        args: "Sequence[VariableTracker]",
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from torch._dynamo.utils import dynamo_timed
        from torch._dynamo.variables.higher_order_ops import (
            _call_function_with_auto_output_flattening,
        )

        fn_var = args[0]
        fn_args_vt = args[1:]

        config = None
        max_reuse_entries = 8
        reuse_hash_fn = None
        if hasattr(fn_var, "get_function"):
            try:
                fn = fn_var.get_function()
                config = getattr(fn, "__marked_compile_region_config__", None)
                max_reuse_entries = getattr(
                    fn, "__marked_compile_region_max_reuse_entries__", 8
                )
                reuse_hash_fn = getattr(
                    fn, "__marked_compile_region_reuse_hash_fn__", None
                )
            except Exception:
                log.warning(
                    "Failed to extract nested_compile_region() config from InvokeSubgraphHigherOrderVariable. ",
                    exc_info=True,
                )
                raise

        # TODO (anijain2305) - Collect issues why this does not work for export,
        # and enable if request arises.
        reuse = not tx.output.export

        # User-provided reuse_hash_fn path: hash key determines cache lookup.
        if reuse and reuse_hash_fn is not None:
            with dynamo_timed("invoke_subgraph_reuse_hash_fn"):
                hash_key = trace_reuse_hash_fn(tx, reuse_hash_fn, fn_args_vt, kwargs)

            cached = find_reuse_entry_by_key(tx, fn_var, hash_key)
            if cached is not None:
                hc_log.debug(
                    "subgraph_reuse: hash key %d hit for '%s', reusing subgraph '%s'",
                    hash_key,
                    fn_var,
                    cached.body_name,
                )
                fingerprint = build_input_fingerprint(tx, fn_args_vt, kwargs)
                with dynamo_timed("invoke_subgraph_reuse_stamp_out"):
                    return stamp_out_subgraph(tx, fingerprint, cached)

        # Automatic reuse lookup (guard-based): check fn_code first (cheap) to
        # avoid the expensive pytree flatten in build_input_fingerprint on
        # the first call when there's nothing in the cache yet.
        elif reuse and has_reuse_entries(tx, fn_var):
            with dynamo_timed("invoke_subgraph_reuse_lookup"):
                fingerprint = build_input_fingerprint(tx, fn_args_vt, kwargs)
                match = find_reuse_match(
                    tx,
                    fn_var,
                    fingerprint,
                )
            if match is not None:
                hc_log.debug(
                    "subgraph_reuse: cache hit for '%s', reusing subgraph '%s'",
                    fn_var,
                    match.body_name,
                )
                with dynamo_timed("invoke_subgraph_reuse_stamp_out"):
                    return stamp_out_subgraph(tx, fingerprint, match)

        assert self._HOP_NAME is not None
        with dynamo_timed("invoke_subgraph_trace"):
            (
                p_args,
                p_kwargs,
                example_value,
                body_r,
                body_gmod,
                body_name,
                body_graph_output_vts,
                tracing_info,
            ) = self.create_wrapped_node(tx, fn_var, fn_args_vt, kwargs, self._HOP_NAME)

        if len(p_kwargs) > 0:
            unimplemented(
                gb_type="invoke_subgraph: kwargs unexpected",
                context=f"args: {args}, kwargs: {kwargs}",
                explanation="kwargs should have been flattened into lifted args.",
                hints=[
                    *graph_break_hints.DYNAMO_BUG,
                ],
            )

        # Store config in the body graph module meta
        if isinstance(config, NestedCompileRegionOptions):
            body_gmod.meta["nested_region_config"] = config

        p_args = (
            p_args[0],
            body_name,
            *p_args[1:],
        )

        # Subgraph reuse: save entry for future cache hits
        if reuse:
            fingerprint = build_input_fingerprint(tx, fn_args_vt, kwargs)
            if reuse_hash_fn is not None:
                traced_sources = tracing_info.traced_sources
                if not is_reuse_eligible(
                    tx,
                    body_r,
                    fingerprint,
                    tracing_info,
                    traced_sources,
                    has_reuse_hash_fn=True,
                ):
                    raise RuntimeError(
                        "reuse_hash_fn was provided but the subgraph is not "
                        "eligible for reuse. Check the logs with "
                        "TORCH_LOGS='+hierarchical_compile' for details."
                    )
                save_reuse_entry(
                    tx,
                    fn_var,
                    fingerprint,
                    body_name,
                    body_gmod,
                    config,
                    p_args,
                    body_r,
                    example_value,
                    max_reuse_entries,
                    hash_key=hash_key,  # type: ignore[possibly-undefined]
                )
            else:
                traced_sources = tracing_info.traced_sources
                if is_reuse_eligible(
                    tx, body_r, fingerprint, tracing_info, traced_sources
                ):
                    condition = build_reuse_condition(
                        tx,
                        fingerprint,
                        traced_sources,
                    )
                    if condition is not None:
                        save_reuse_entry(
                            tx,
                            fn_var,
                            fingerprint,
                            body_name,
                            body_gmod,
                            config,
                            p_args,
                            body_r,
                            example_value,
                            max_reuse_entries,
                            condition=condition,
                        )

        return _call_function_with_auto_output_flattening(  # type: ignore[return-value]
            tx,
            torch._higher_order_ops.invoke_subgraph,
            tuple(p_args),
            p_kwargs,
            example_value,
            body_r,
            body_graph_output_vts,
            config=config,
        )