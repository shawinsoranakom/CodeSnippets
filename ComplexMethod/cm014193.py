def save_reuse_entry(
    tx: "InstructionTranslator",
    fn_var: Any,
    fingerprint: InputFingerprint,
    body_name: str,
    body_gmod: torch.fx.GraphModule,
    config: NestedCompileRegionOptions | None,
    p_args: tuple[Any, ...],
    body_r: VariableTracker,
    example_value: Any,
    max_reuse_entries: int = 8,
    condition: "InvokeSubgraphReuseCondition | None" = None,
    hash_key: int | None = None,
) -> None:
    """Save a traced subgraph into the reuse cache for future cache hits.

    Builds an InvokeSubgraphReuseEntry with the freevar mapping (how each
    lifted arg maps back to user inputs or captured variables), output
    metadata, and arg sources. On a future cache hit, stamp_out_subgraph
    uses this entry to emit a new invoke_subgraph call without re-tracing.

    Exactly one of ``condition`` or ``hash_key`` must be provided.
    ``condition`` stores the entry in the guard-based cache (linear scan);
    ``hash_key`` stores it in the hash-key cache (O(1) lookup).
    """
    from torch._guards import InvokeSubgraphCache

    assert (condition is None) != (hash_key is None), (
        "Exactly one of condition or hash_key must be provided"
    )

    invoke_subgraph_cache = tx.output.tracing_context.hop_dispatch_set_cache.get_cache(
        torch._higher_order_ops.invoke_subgraph
    )
    if not isinstance(invoke_subgraph_cache, InvokeSubgraphCache):
        return

    fn_code = get_fn_code(fn_var)
    if fn_code is None:
        return

    subgraph_input_mapping = build_subgraph_input_mapping(
        tx, p_args, fingerprint.flat_vts
    )
    single_tensor_output = isinstance(body_r, TensorVariable)

    # Count user-visible outputs from body_r. The graph may have additional
    # outputs from side-effect intermediates that stamp_out_subgraph must
    # not include when reconstructing the user-visible return value.
    user_output_vts: list[VariableTracker] = []
    VariableTracker.visit(
        lambda vt: user_output_vts.append(vt)
        if vt.is_tensor() or isinstance(vt, SymNodeVariable)
        else None,
        body_r,
    )
    num_user_outputs = len(user_output_vts)

    # Cache output tensor metadata so we can construct fresh FakeTensors on
    # cache hit without re-running the subgraph. This is safe because
    # invoke_subgraph does not support aliasing between inputs and outputs
    # (speculate_subgraph will fail if that happens).
    # example_value may contain SymInts (e.g. shape values for backward);
    # only record metadata for actual tensors.
    output_metadata = [
        (t.shape, t.stride(), t.dtype, t.device, t.requires_grad)
        for t in example_value
        if isinstance(t, torch.Tensor)
    ]

    entry = InvokeSubgraphReuseEntry(
        body_name=body_name,
        body_gmod=body_gmod,
        config=config,
        subgraph_input_mapping=subgraph_input_mapping,
        single_tensor_output=single_tensor_output,
        output_metadata=output_metadata,
        # Record arg sources so that on cache hit we can build a
        # source replacement mapping (old sources → new sources) to
        # rewrite captured variable sources for the current invocation.
        arg_sources=fingerprint.arg_sources,
        num_user_outputs=num_user_outputs,
    )
    if condition is not None:
        invoke_subgraph_cache.add_reuse_entry(
            fn_code, condition, entry, max_reuse_entries
        )
    else:
        assert hash_key is not None
        invoke_subgraph_cache.add_reuse_entry_by_key(
            fn_code, hash_key, entry, max_reuse_entries
        )