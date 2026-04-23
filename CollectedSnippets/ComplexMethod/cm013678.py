def _extract_closure_pytree(
    fn, _seen: set[int] | None = None
) -> tuple[
    tuple[BaseArgumentTypes, ...], TreeSpec, _StrippedClosure | Callable[..., Any]
]:
    """Extract closure contents as a flattened sub-pytree.

    Returns (extracted_leaves, closure_spec, fn_or_stripped) where:
    - extracted_leaves: flattened non-function contents from the closure,
      plus any tensors/scalars recursively extracted from nested function
      closures
    - closure_spec: TreeSpec describing how to reconstruct the closure contents
    - fn_or_stripped: either the original fn (no extraction) or a
      _StrippedClosure carrying the function parts needed for reconstruction

    Functions found among the closure leaves are recursively processed: their
    own closure tensors are extracted into the leaves list, and their skeleton
    is stored in _StrippedClosure.leaf_entries as a _FunctionLeaf.  All other
    values (tensors, scalars, None, etc.) remain as extracted leaves.

    If fn is not a plain function, has no closure, or has empty cells, returns
    the original function unchanged with no closure leaves.

    Skipped under Dynamo tracing (torch.compiler.is_compiling) because Dynamo
    can't trace through closure cell introspection and handles freevars via its
    own lifting mechanism.
    """
    if not inspect.isfunction(fn) or torch.compiler.is_compiling():
        return (), _EMPTY_CLOSURE_SPEC, fn

    # Cycle detection for self-referencing closures.
    if _seen is None:
        _seen = set()
    if id(fn) in _seen:
        return (), _EMPTY_CLOSURE_SPEC, fn
    _seen.add(id(fn))

    closure = fn.__closure__
    if not closure:
        return (), _EMPTY_CLOSURE_SPEC, fn

    try:
        contents = tuple(cell.cell_contents for cell in closure)
    except ValueError:
        # Empty cell (created but not yet assigned) — can't extract
        return (), _EMPTY_CLOSURE_SPEC, fn

    closure_leaves, closure_spec = tree_flatten(contents)

    extracted: list[BaseArgumentTypes] = []
    leaf_entries: list[_ExtractedLeaf | _FunctionLeaf] = []
    for leaf in closure_leaves:
        if inspect.isfunction(leaf):
            child_extracted, child_spec, child_stripped = _extract_closure_pytree(
                leaf, _seen
            )
            extracted.extend(child_extracted)
            leaf_entries.append(
                _FunctionLeaf(child_stripped, child_spec, len(child_extracted))
            )
        else:
            extracted.append(leaf)
            leaf_entries.append(_EXTRACTED_LEAF)

    stripped = _StrippedClosure(
        code=fn.__code__,
        globals_dict=fn.__globals__,
        name=fn.__name__,
        qualname=fn.__qualname__,
        defaults=fn.__defaults__,
        kwdefaults=fn.__kwdefaults__,
        extra_dict=dict(fn.__dict__) if fn.__dict__ else {},
        leaf_entries=tuple(leaf_entries),
    )

    return tuple(extracted), closure_spec, stripped