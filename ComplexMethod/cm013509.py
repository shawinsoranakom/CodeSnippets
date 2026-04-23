def _free_unbacked_symbols_with_path(
    a: object,
    path: pytree.KeyPath,
    real: object | None = None,
    shape_env: ShapeEnv | None = None,
    pending: set[sympy.Symbol] | None = None,
    simplify: bool = False,
) -> dict[sympy.Symbol, pytree.KeyPath]:
    """
    Recursively traverses a structure to find unbacked symbols and their access paths.

    This function walks through tensors, lists, tuples, and symbolic values to locate
    unbacked symbols that are in the pending set, and returns a mapping from those
    symbols to their access paths in the structure.

    Args:
        a: The object to traverse (tensor, list, tuple, SymInt, etc.)
        path: The current path in the object tree
        real: Optional real tensor corresponding to the fake tensor being traversed
        shape_env: Optional ShapeEnv to register unbacked values with
        pending: Set of unbacked symbols to look for (will be modified in-place)
        simplify: Whether to use simplified expressions

    Returns:
        A dictionary mapping unbacked symbols to their access paths
    """
    go = functools.partial(
        _free_unbacked_symbols_with_path,
        shape_env=shape_env,
        pending=pending,
        simplify=simplify,
    )

    def expr(s: SymInt | SymFloat | SymBool) -> sympy.Expr:
        if simplify:
            return s.node.expr
        # (When called from compute_unbacked_bindings)
        # NB: Intentionally access _expr, not expr, do not want
        # simplification!
        return s.node._expr

    if pending is None:
        pending = set()
    r = {}

    def match_tensor(a: torch.Tensor, real_tensor: torch.Tensor | None = None) -> None:
        r.update(
            go(
                a.size(),
                path + (CallMethodKey("size"),),
                real=real_tensor.size() if real_tensor is not None else None,
            )
        )
        if a.layout not in [
            torch.sparse_csr,
            torch.sparse_csc,
            torch.sparse_bsr,
            torch.sparse_bsc,
        ]:
            r.update(
                go(
                    a.stride(),
                    path + (CallMethodKey("stride"),),
                    real=real_tensor.stride() if real_tensor is not None else None,
                )
            )
        r.update(
            go(
                a.storage_offset(),
                path + (CallMethodKey("storage_offset"),),
                real=(
                    real_tensor.storage_offset() if real_tensor is not None else None
                ),
            )
        )

    if isinstance(a, (tuple, list)):
        # NB: real is apparently not always a tuple/list here
        # python test/inductor/test_torchinductor.py CpuTests.test_index_propagation_nested_indirect_indexing_cpu
        for i in range(len(a)):
            r.update(
                go(
                    a[i],
                    path + (pytree.SequenceKey(i),),
                    real=real[i] if real is not None else None,  # type: ignore[index]
                )
            )
    elif is_traceable_wrapper_subclass(a):
        # TODO: Determine if this is correct
        attrs, _ = a.__tensor_flatten__()
        for attr in attrs:
            sub = getattr(a, attr)
            r.update(go(sub, path + (InnerTensorKey(attr),)))

        # match DTensor outer shapes
        if torch.distributed.is_available() and isinstance(
            a, torch.distributed.tensor.DTensor
        ):
            match_tensor(a)
    elif isinstance(a, torch.Tensor) and (
        is_batchedtensor(a) or is_gradtrackingtensor(a)
    ):
        unwrapped_tensor = get_unwrapped(a)
        r.update(go(unwrapped_tensor, path))
    elif (
        isinstance(a, torch.Tensor)
        and not is_batchedtensor(a)
        and not is_gradtrackingtensor(a)
    ):
        from torch._subclasses.fake_tensor import FakeTensor

        if not isinstance(a, FakeTensor):
            raise AssertionError(f"Expected FakeTensor, got {type(a)}")
        match_tensor(a, a.real_tensor)
    elif (
        isinstance(a, (torch.SymInt, torch.SymFloat))
        and isinstance(s := expr(a), sympy.Symbol)
        and s in pending
    ):
        r[s] = path
        if shape_env and real is not None:
            if not isinstance(real, (int, float)):
                raise AssertionError(f"Expected int or float, got {type(real)}")

            shape_env.set_real_tensor_prop_unbacked_vals(s, real)

        pending.remove(s)
    # When an unbacked SymInt is perfectly divisible by an integer
    # constant, we replace it with the integer constant to improve
    # reasoning capabilities.  However, in synthetic examples, it is
    # then possible that the factor never is explicitly allocated.
    # Fortunately, we can compute it by division.
    elif (
        isinstance(a, torch.SymInt)
        and isinstance(s := expr(a), sympy.Mul)
        and len(s.args) == 2
        and isinstance(lhs := s.args[0], (sympy.Integer, sympy.Symbol))
        and isinstance(rhs := s.args[1], sympy.Symbol)
        # support exactly one unbacked for now
        and ((rhs in pending) ^ (lhs in pending))
        # support constant coefficient or backed symbolic coefficient
        and (
            isinstance(coeff := lhs if lhs not in pending else rhs, sympy.Integer)
            or shape_env
            and coeff in shape_env.backed_var_to_val
        )
    ):

        def _symint_wrap(s: sympy.Symbol) -> SymInt:
            return shape_env.create_symintnode(  # type: ignore[union-attr]
                s,
                hint=int(shape_env.backed_var_to_val[s]),  # type: ignore[union-attr]
                source=shape_env.var_to_sources.get(s, [None])[0],  # type: ignore[union-attr]
            )

        unbacked = lhs if lhs in pending else rhs
        divisor: IntLikeType = (
            int(coeff)
            if shape_env and isinstance(coeff, sympy.Integer)
            else _symint_wrap(coeff)
        )
        # TODO: DivideByKey needs to test divisibility at runtime!

        # pyrefly: ignore [unsupported-operation]
        r[unbacked] = path + (DivideByKey(divisor),)
        if real is not None:
            if not isinstance(real, int):
                raise AssertionError(f"Expected int, got {type(real)}")
            val = (
                real // int(coeff)
                if isinstance(coeff, sympy.Integer)
                else CleanDiv(real, coeff)
            )
            if shape_env:
                shape_env.set_real_tensor_prop_unbacked_vals(unbacked, val)
        pending.remove(unbacked)
    # The annoyance here arises from the fact that SymBool is
    # allocated by allocating a SymInt and then testing if it's equal
    # to one.  So you have a complicated binding site logic for this.
    elif (
        isinstance(a, torch.SymBool)
        and isinstance(s := expr(a), sympy.Eq)
        # This must match create_unbacked_symbool EXACTLY
        and isinstance(s.lhs, sympy.Symbol)
        and s.rhs == 1
        and s.lhs in pending
    ):
        # pyrefly: ignore [unsupported-operation]
        r[s.lhs] = path + (ConvertIntKey(),)
        if real is not None:
            if type(real) is not bool:
                raise AssertionError(f"Expected bool, got {type(real)}")
            if shape_env:
                shape_env.set_real_tensor_prop_unbacked_vals(s, int(real))

        pending.remove(s.lhs)

    return r