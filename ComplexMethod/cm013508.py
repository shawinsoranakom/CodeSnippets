def _iterate_nodes(val: Any) -> Iterator[SymNode]:
    """
    Recursively iterate through a value and yield all SymNodes contained
    within it.
    """
    if isinstance(val, SymNode):
        yield val
    elif isinstance(val, py_sym_types):
        # This allow applies to the jagged layout NestedTensor case as
        # nested ints are not symbolic
        if is_symbolic(val):
            yield val.node
    elif isinstance(val, (tuple, list, torch.Size)):
        for s in val:
            yield from _iterate_nodes(s)
    elif isinstance(val, torch.Tensor):
        yield from _iterate_nodes(val.size())
        if not is_sparse_any(val):
            yield from _iterate_nodes(val.stride())
            yield from _iterate_nodes(val.storage_offset())