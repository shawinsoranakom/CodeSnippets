def _iterate_exprs(val: IterateExprs) -> Iterator[sympy.Basic]:
    """
    Recursively iterate through a value and yield all sympy expressions contained within it.

    This function traverses various data structures (tensors, lists, tuples, etc.) and extracts
    any symbolic expressions they contain. It's used for operations like finding free symbols
    in complex nested structures.

    Args:
        val: The value to extract sympy expressions from. Can be a symbolic type (SymInt, SymFloat, SymBool),
             a sympy expression, a primitive type (int, float, bool), a container (tuple, list),
             a sparse tensor, a regular tensor, None, or a torch.Generator.

    Yields:
        sympy.Basic: Each sympy expression found in the value.

    Raises:
        AssertionError: If the value is of an unsupported type.
    """
    # This is almost close enough to implement in terms of _iterate_nodes()
    # except that it needs to handle `list[sympy.Basic]` which _iterate_nodes()
    # can't handle.
    if isinstance(val, SymTypes):
        # This allow applies to the jagged layout NestedTensor case as
        # nested ints are not symbolic
        if is_symbolic(val):
            yield val.node.expr
    elif isinstance(val, SymNode):
        yield val.expr
    elif isinstance(val, sympy.Basic):
        yield val
    elif isinstance(val, (int, float, bool, str)):
        pass
    elif isinstance(val, (tuple, list)):
        for s in val:
            yield from _iterate_exprs(s)
    elif isinstance(val, dict):
        for s in itertools.chain(val.keys(), val.values()):
            yield from _iterate_exprs(s)
    elif is_sparse_any(val):
        yield from _iterate_exprs(val.size())
    elif isinstance(val, torch.Tensor):
        yield from _iterate_exprs(val.size())
        yield from _iterate_exprs(val.stride())
        yield from _iterate_exprs(val.storage_offset())
    elif val is None:
        pass
    # see Note: [Generator arguments in AOTDispatcher]
    elif isinstance(val, torch.Generator) or is_opaque_value(val):
        pass
    elif isinstance(val, FakeScriptObject):
        pass
    else:
        raise AssertionError(f"cannot extract sympy expressions from {val} {type(val)}")