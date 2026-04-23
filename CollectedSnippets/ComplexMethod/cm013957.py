def maybe_setup_comprehension_speculation(
    tx: InstructionTranslatorBase, inst: Instruction
) -> bool:
    """
    Handle comprehension start for Python 3.12+ BUILD_LIST/BUILD_MAP with argval 0.
    Returns True if a graph break was triggered and the caller should return early.
    """
    if not (sys.version_info >= (3, 12) and inst.argval == 0):
        return False

    if not _is_comprehension_start(tx):
        return False

    can_speculate = (
        all(b.can_restore() for b in tx.block_stack)
        and not tx.one_graph
        and not tx.error_on_graph_break
        and not tx.is_tracing_resume_prologue
        and not tx.active_generic_context_managers
        and tx.output.current_tracer.parent is None
    )

    if can_speculate and tx.parent is not None:
        can_speculate = tx._can_speculate_comprehension_nested()
    # Only set up speculation at depth 0 (outermost comprehension)
    if can_speculate and tx._comprehension_depth == 0:
        speculation = tx.speculate()
        if speculation.failed(tx):
            _handle_comprehension_graph_break(tx, inst)
            return True
        tx.current_speculation = speculation
    end_for_ip = _find_comprehension_end_for_ip(tx)
    assert end_for_ip >= 0
    tx._comprehension_end_for_ips.add(end_for_ip)
    tx._comprehension_depth += 1
    return False