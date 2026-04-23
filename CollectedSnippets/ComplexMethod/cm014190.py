def is_reuse_eligible(
    tx: "InstructionTranslator",
    body_r: Any,
    fingerprint: InputFingerprint,
    tracing_info: "SubgraphTracingInfo",
    traced_sources: OrderedSet[Source] | None = None,
    has_reuse_hash_fn: bool = False,
) -> bool:
    """Best-effort check for whether a traced subgraph result can be reused.

    It is possible that a subgraph is morally reusable but does not fall
    into the limited support that Dynamo has today. Current limitations:
      - The subgraph must not have side effects.
      - No sourceful variable accessed by the subgraph may have been
        mutated, because guards are snapshotted on source values at trace
        time — if the underlying object changed since then, the cached
        guards would silently evaluate against stale values.
      - Output must be a single tensor, or a tuple/list of plain tensors.
      - All flattened inputs must be one of: tensor, symnode, constant,
        unspecialized NN module — for sourceless or other input types we
        rely on the treespec and tags for structural matching, so only
        types with well-defined comparison semantics are supported.

    When ``has_reuse_hash_fn`` is True, side-effect and mutation checks are
    skipped because the hash key replaces guards — there are no guards to
    go stale from mutations.
    """
    if not has_reuse_hash_fn:
        if tracing_info.side_effect_stack is not None:
            stack_msg = "\n" + "".join(
                traceback.format_list(tracing_info.side_effect_stack)
            )
            hc_log.debug(
                "subgraph_reuse: not eligible -- subgraph has side effects%s",
                stack_msg,
            )
            return False

        if traced_sources and has_mutated_vars(tx, traced_sources):
            return False

    if isinstance(body_r, TensorVariable):
        pass
    elif isinstance(body_r, (TupleVariable, ListVariable)):
        non_tensor = [
            type(item).__name__
            for item in body_r.items
            if not isinstance(item, TensorVariable)
        ]
        if non_tensor:
            hc_log.debug(
                "subgraph_reuse: not eligible -- output contains non-tensor types: %s",
                non_tensor,
            )
            return False
    else:
        hc_log.debug(
            "subgraph_reuse: not eligible -- output type %s is not tensor or tuple/list",
            type(body_r).__name__,
        )
        return False

    if fingerprint.has_unknown:
        hc_log.debug(
            "subgraph_reuse: not eligible -- unsupported input VT types",
        )
        return False

    return True