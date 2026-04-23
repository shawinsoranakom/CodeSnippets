def slice_(x, dim=0, start=0, end=sys.maxsize, step=1, clamp=True):
    """
    Lowers a slice call, creating ExternKernels for the output size & storage offset symbols,
    if the indices are unbacked and appropriate semantics aren't known.
    If they are known (indices are static/backed/unbacked with info), a SliceView is created.
    """

    from torch.fx.experimental.symbolic_shapes import (
        CallMethodKey,
        resolve_unbacked_bindings,
    )

    assert isinstance(x, TensorBox)
    dim = _validate_dim(x, dim, 0)
    size = x.get_size()[dim]
    step = sympy.expand(step)
    assert isinstance(step, sympy.Expr) or step > 0, step

    # maybe apply slice optimization
    try:
        if (
            start == 0
            and V.graph.sizevars.statically_known_leq(size, end)
            and step == 1
        ):
            return x
    except TypeError:
        pass

    # try to avoid dynamic (unbacked) slice
    def compute_slice_index(index, size, default=None):
        if index is None:
            return default

        fn = lambda x: V.graph.sizevars.guard_or_false(x)  # noqa: E731
        index = sympy.expand(index)
        size = sympy.expand(size)
        if fn(sympy.And(sympy.Ge(index, 0), sympy.Le(index, size))):
            return index
        elif fn(sympy.And(sympy.Lt(index, 0), sympy.Ge(index, -size))):
            return index + size
        elif fn(sympy.Gt(index, size)):
            return size
        elif fn(sympy.Lt(index, -size)):
            return 0
        elif fn(sympy.Ge(index, 0)):
            # If index >= 0, the resolved index is at most min(index, size).
            return sympy.Min(index, size)
        elif fn(sympy.Lt(index, 0)):
            # If index < 0, wrap and clamp: the resolved index is at least 0.
            return sympy.Max(index + size, 0)
        return None

    start_index, end_index = None, None
    # ambiguous_slice=False means we know what semantics this slice call follows,
    # and don't need to generate an extern kernel to represent the output size.
    # This is assumed True for clamp=False
    # (meant to follow standard indexing semantics: 0 <= index < size)
    ambiguous_slice = clamp
    if ambiguous_slice:
        start_index = compute_slice_index(start, size, 0)
        # Special case: if end is maxsize (unbounded), use size directly
        # This matches the logic in fake_impls.py
        if end is not None and V.graph.sizevars.statically_known_equals(
            end, sys.maxsize
        ):
            end_index = size
        else:
            end_index = compute_slice_index(end, size, size)
        if start_index is not None and end_index is not None:
            start, end = start_index, end_index
            ambiguous_slice = False

    if not ambiguous_slice:
        # Even though the bounds are resolvable now, the FX node may have
        # allocated unbacked symbols for the slice output size because dynamo
        # couldn't prove the bounds at trace time (constraints may have been
        # learned after tracing the slice). We still need to define those
        # symbols so the assertion new_unbacked_defs >= renamed_unbacked_bindings
        # passes. Register a DynamicSliceSize operation to define the size symbol.
        # Note: storage_offset bindings should not appear here because
        # a resolved start_index means the offset is computable directly
        # (base_offset + start * stride), so dynamo wouldn't allocate an
        # unbacked symbol for it.
        # Note: current_node may be None when slice_ is called from template
        # rendering (e.g. cpp_template_kernel.slice_nd) rather than FX graph
        # lowering, so we handle that.
        current_node = V.graph.current_node
        node_unbacked_bindings = resolve_unbacked_bindings(
            V.graph.sizevars.shape_env,
            current_node.meta.get("unbacked_bindings", {})
            if current_node is not None
            else {},
        )
        if node_unbacked_bindings:
            for sym, keypath in node_unbacked_bindings.items():
                if keypath == (CallMethodKey("size"), pytree.SequenceKey(dim)):
                    b_size = ir.DynamicSliceSize(sym, start, end, step, size)
                    b_size.name = V.graph.register_buffer(b_size)
                    V.graph.register_operation(b_size)
                elif keypath == (CallMethodKey("storage_offset"),):
                    # Not handled yet — would require materializing the
                    # tensor layout. Unlikely to be hit because a resolved
                    # start_index means the offset is computable directly.
                    raise AssertionError(
                        "Unexpected storage_offset unbacked binding when both "
                        "start and end indices are resolved"
                    )

        return TensorBox(
            ir.SliceView.create(x.data, dim, start, end, step, clamp=clamp)
        )  # go to SliceView/ReinterpretView

    # unbacked territory: create DynamicSlice ExternKernel
    # clamp is True, unbacked start / end
    assert clamp
    unbacked_bindings = resolve_unbacked_bindings(
        V.graph.sizevars.shape_env, V.graph.current_node.meta["unbacked_bindings"]
    )
    assert unbacked_bindings is not None
    assert len(unbacked_bindings) <= 2, unbacked_bindings
    sym_size, sym_storage = None, None
    for sym, keypath in unbacked_bindings.items():
        if keypath == (CallMethodKey("size"), pytree.SequenceKey(dim)):
            sym_size = sym
        elif keypath == (CallMethodKey("storage_offset"),):
            sym_storage = sym

    assert start_index is None or end_index is None
    b_size = ir.DynamicSliceSize(
        sym_size,
        start,
        end,
        step,
        x.get_size()[dim],
    )
    b_size.name = V.graph.register_buffer(b_size)
    V.graph.register_operation(b_size)
    new_size = sym_size

    if x.maybe_get_layout() is None:
        # realize tensor before accessing layout
        x.realize()

    if start_index is not None:
        # we shouldn't have allocated storage offset symbol if start index was determinable
        assert sym_storage is None
        new_storage_offset = x.get_layout().offset + start_index * x.get_stride()[dim]
    else:
        b_storage = ir.DynamicSelectStorageOffset(
            sym_storage,
            start,
            x.get_layout().offset,
            x.get_stride()[dim],
            x.get_size()[dim],
            clamp=True,
        )
        b_storage.name = V.graph.register_buffer(b_storage)
        V.graph.register_operation(b_storage)
        new_storage_offset = sym_storage

    new_sizes = list(x.get_size())
    new_strides = list(x.get_stride())
    new_sizes[dim] = new_size
    new_strides[dim] *= step
    return as_strided(x, new_sizes, new_strides, new_storage_offset)