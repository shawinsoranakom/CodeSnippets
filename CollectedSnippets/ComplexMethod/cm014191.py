def build_reuse_condition(
    tx: "InstructionTranslator",
    fingerprint: InputFingerprint,
    traced_sources: OrderedSet[Source],
) -> InvokeSubgraphReuseCondition | None:
    """Build an InvokeSubgraphReuseCondition from a traced subgraph.

    A reuse condition is a mix of two kinds of checks:

    1. **Input tag checks** (from flat_vts): For each flattened leaf VT,
       we record its tag (_VtTag.TENSOR/SYMNODE/CONSTANT/MODULE) and
       metadata (e.g. tensor shape/stride/dtype/device/requires_grad).
       At lookup time, the treespec ensures structural equivalence, and
       then we compare tags and metadata leaf-by-leaf.

    2. **Guard checks** (from traced_sources): During the subgraph trace,
       every source accessed via VariableBuilder is recorded. We look up
       all guards installed on those sources (and on the arg_sources) to
       build the set of guards that must be re-evaluated on cache hit.
       This is more robust than guard diffing because it catches guards
       that were already installed before the subgraph trace began.

    Raise if any guard type is unsupported, as a feedback for compiler
    developers to support that guard type.
    """
    from torch._guards import InvokeSubgraphReuseCondition

    input_checks: list[tuple[InputTag, object]] = []
    for tag, vt in fingerprint.flat_vts:
        if tag == InputTag.TENSOR:
            assert isinstance(vt, TensorVariable)
            example = vt.proxy.node.meta.get("example_value", None)
            if example is None:
                hc_log.debug(
                    "subgraph_reuse: cannot build condition -- tensor input has no example_value"
                )
                return None
            input_checks.append((InputTag.TENSOR, extract_tensor_metadata(example)))
        elif tag == InputTag.SYMNODE:
            assert isinstance(vt, SymNodeVariable)
            # Store the SymInt/SymFloat/SymBool object itself. Two accesses to
            # the same symbolic dimension (e.g. x.shape[0] twice) produce the
            # same Python object, so identity comparison in is_reusable is
            # correct and avoids false matches between distinct symbols.
            input_checks.append((InputTag.SYMNODE, vt.sym_num))
        elif tag == InputTag.CONSTANT:
            assert isinstance(vt, ConstantVariable)
            input_checks.append((InputTag.CONSTANT, vt.value))
        elif tag == InputTag.MODULE:
            input_checks.append((InputTag.MODULE, None))
        else:
            raise AssertionError(
                f"Unexpected input tag '{tag}' for {type(vt).__name__} -- "
                f"is_reuse_eligible should have rejected this"
            )

    # Collect all guards for sources accessed during the subgraph trace
    # and for the flattened arg sources.
    all_sources = set(traced_sources)
    all_sources.update(s for s in fingerprint.arg_sources if s is not None)
    all_relevant_guards: set[Guard] = set()
    for source in all_sources:
        all_relevant_guards.update(tx.output.guards.get_guards_for_source(source))

    guard_tuples: list[tuple[Source, GuardCheckSpec, object, Guard]] = []
    for guard in all_relevant_guards:
        source = guard.originating_source
        type_str = guard.create_fn_name()
        handler = GUARD_VALUE_DISPATCH.get(type_str)

        if handler is SKIP_GUARD:
            continue

        if handler is None or isinstance(handler, UnsupportedGuardCheckSpec):
            raise RuntimeError(
                f"subgraph_reuse: unsupported guard type '{type_str}' on source '{source.name}'"
            )

        try:
            value = tx.output.resolve_source_value(source)
        except Exception:
            raise RuntimeError(
                f"subgraph_reuse: failed to resolve source '{source.name}' for {type_str} guard"
            ) from None

        # TODO(anijain2305): vLLM workaround -- skip CONSTANT_MATCH on
        # strings. Re-evaluate once vLLM migrates off this pattern.
        # if type_str == "CONSTANT_MATCH" and isinstance(value, str):
        #     continue

        handler = cast(GuardCheckSpec, handler)
        expected = handler.get_metadata_fn(guard, value)
        guard_tuples.append((source, handler, expected, guard))

    hc_log.debug("Number of guards %s", len(guard_tuples))

    return InvokeSubgraphReuseCondition(
        input_checks=input_checks,
        guards=guard_tuples,
        treespec=fingerprint.treespec,
        traced_sources=traced_sources,
    )