def extract_loop_body_with_args(
    fn: Any,
    args: list[list[sympy.Expr]],
    var_ranges: VarRanges,
    normalize: bool = False,
) -> _RecordLoadStoreInner:
    from .loop_body import MemoryUsageType

    # Fast path to avoid tracing when we already have a LoopBody
    inner = _RecordLoadStoreInner(var_ranges=var_ranges, normalize=normalize)
    name_to_index = fn.indexing_from_args(args)
    if fn.indirect_vars:
        # mimic the `tmpX` naming tracing gives us
        repl = {v: make_symbol(SymT.TMP, i) for i, v in enumerate(fn.indirect_vars)}
        name_to_index = {k: sympy_subs(v, repl) for k, v in name_to_index.items()}  # type: ignore[arg-type]
    for entry in fn.memory_usage[MemoryUsageType.LOAD]:
        inner.load(entry.buffer_name, name_to_index[entry.index_name])  # type: ignore[arg-type]
    for entry in fn.memory_usage[MemoryUsageType.LOAD_SEED]:
        inner.load_seed(entry.buffer_name, int(name_to_index[entry.index_name]))  # type: ignore[arg-type]
    for entry in fn.memory_usage[MemoryUsageType.STORE]:
        inner.store(
            entry.buffer_name,
            name_to_index[entry.index_name],
            None,  # type: ignore[arg-type]
            entry.mode,
        )
    for entry in fn.memory_usage[MemoryUsageType.STORE_REDUCTION]:
        inner.store_reduction(
            entry.buffer_name,
            name_to_index[entry.index_name],
            None,  # type: ignore[arg-type]
        )
    for entry in fn.memory_usage[MemoryUsageType.INDEX_EXPR]:
        inner.index_expr(name_to_index[entry.index_name], None)
    for entry in fn.memory_usage[MemoryUsageType.BUCKETIZE]:
        # All that matters is that we record the buffer name, so place it in the
        # "boundaries" name position to ensure that it's recorded.
        inner.bucketize(
            None,
            (entry.buffer_name, None, None, None),
            None,
            None,  # type: ignore[arg-type]
            None,  # type: ignore[arg-type]
        )
    # fn.memory_usage[MemoryUsageType.CHECK_BOUNDS] intentionally skipped
    return inner