def is_reusable(
    tx: "InstructionTranslator",
    condition: "InvokeSubgraphReuseCondition",
    fingerprint: InputFingerprint,
    cached_entry: InvokeSubgraphReuseEntry,
) -> bool:
    """Check if a cached subgraph can be reused for the current call.

    Three-phase check:
    (1) Verify that intermediates (tensor metadata, symnode types, constant
        values) match the cached input_checks — these are lightweight
        structural comparisons that don't require source resolution.
    (2) Check for mutations on the remapped traced_sources — if any source
        the subgraph read has been mutated since the original trace, the
        cached guards would evaluate against stale values.
    (3) Build a source replacement mapping (old sources → new sources) and
        re-evaluate the snapshotted guards under the new sources.
    """
    # Structural check: treespec must match first.
    if condition.treespec is not None and fingerprint.treespec != condition.treespec:
        hc_log.debug(
            "subgraph_reuse: reuse failed -- treespec mismatch",
        )
        return False

    # Input count, tags, and metadata must match.
    # Tensor metadata (shape, stride, dtype, device, requires_grad) is checked
    # here because TENSOR_MATCH guards for subgraph inputs typically already
    # exist in the outer graph before tracing and thus won't appear in the
    # guard delta.
    if len(condition.input_checks) != len(fingerprint.flat_vts):
        hc_log.debug(
            "subgraph_reuse: reuse failed -- input count mismatch: cached %d vs current %d",
            len(condition.input_checks),
            len(fingerprint.flat_vts),
        )
        return False

    for i, ((cached_tag, cached_val), (cur_tag, cur_vt)) in enumerate(
        zip(condition.input_checks, fingerprint.flat_vts)
    ):
        if cached_tag != cur_tag:
            hc_log.debug(
                "subgraph_reuse: reuse failed -- input %d tag mismatch: cached '%s' vs current '%s'",
                i,
                cached_tag,
                cur_tag,
            )
            return False
        if cached_tag == InputTag.TENSOR:
            assert isinstance(cur_vt, TensorVariable)
            example = cur_vt.proxy.node.meta.get("example_value", None)
            if example is None:
                hc_log.debug(
                    "subgraph_reuse: reuse failed -- input %d tensor has no example_value",
                    i,
                )
                return False
            cur_meta = extract_tensor_metadata(example)
            if cur_meta != cached_val:
                hc_log.debug(
                    "subgraph_reuse: reuse failed -- input %d tensor metadata mismatch",
                    i,
                )
                return False
        elif cached_tag == InputTag.SYMNODE:
            assert isinstance(cur_vt, SymNodeVariable)
            if cur_vt.sym_num is not cached_val:
                return False
        elif cached_tag == InputTag.CONSTANT:
            assert isinstance(cur_vt, ConstantVariable)
            if cur_vt.value != cached_val:
                # If both the cached and current arg have sources, source
                # replacement in stamp_out will resolve the correct value.
                cached_src = (
                    cached_entry.arg_sources[i]
                    if i < len(cached_entry.arg_sources)
                    else None
                )
                new_src = (
                    fingerprint.arg_sources[i]
                    if i < len(fingerprint.arg_sources)
                    else None
                )
                if cached_src is None or new_src is None:
                    return False

    source_replacement = build_source_replacement(
        cached_entry.arg_sources, fingerprint.arg_sources
    )

    # Parameterized source - this function gives you new sources parameterized
    # on the arg_sources. For example, if the input to the nested compile region
    # is a nn Module layer with source `layers[0]`, then old source
    # `layers[0].weight` gets remapped to `layers[1].weight`. This
    # parameterization is central in getting the new sources and then running
    # guards on them.
    def replacement_fn(s: Source) -> Source:
        return source_replacement.get(s, s)

    # Check for mutations on remapped traced_sources.
    if source_replacement:
        remapped = OrderedSet(s.clone(replacement_fn) for s in condition.traced_sources)
    else:
        remapped = condition.traced_sources
    if has_mutated_vars(tx, remapped):
        return False

    # If no sources changed, all guards were already checked during the
    # original trace and will trivially pass again.
    if not source_replacement:
        return True

    # Shared resolution context so source.get_value memoizes intermediate
    # results (e.g. common base sources) across all guards in this check.
    resolve_globals: dict[str, Any] = {
        "G": tx.output.root_tx.f_globals,
        "L": tx.output.root_tx.f_locals,
    }
    resolve_locals: dict[str, Any] = {}
    resolve_cache: dict[Source, Any] = {}

    for source, handler, expected, guard in condition.guards:
        new_source = source.clone(replacement_fn)
        # Source unchanged after replacement — guard already passed during
        # the original trace, skip re-evaluation.
        if new_source == source:
            continue

        try:
            value = new_source.get_value(resolve_globals, resolve_locals, resolve_cache)
        except Exception:
            hc_log.debug(
                "subgraph_reuse: reuse failed -- cannot resolve source\n"
                "  guard type: %s\n"
                "  guard source: %s\n"
                "  guard source name: %s\n"
                "  user stack:\n%s",
                guard.create_fn_name(),
                new_source,
                new_source.name,
                "".join(guard.user_stack.format())
                if guard.user_stack
                else "<no stack>",
            )
            return False

        if not handler.eval_fn(value, expected):
            hc_log.debug(
                "subgraph_reuse: reuse failed --\n"
                "  guard type: %s\n"
                "  guard source: %s\n"
                "  guard source name: %s\n"
                "  expected: %s\n"
                "  got: %s\n"
                "  user stack:\n%s",
                guard.create_fn_name(),
                new_source,
                new_source.name,
                expected,
                value,
                "".join(guard.user_stack.format())
                if guard.user_stack
                else "<no stack>",
            )
            return False

    return True