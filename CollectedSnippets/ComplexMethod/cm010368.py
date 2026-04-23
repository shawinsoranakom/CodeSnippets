def _merge_output(
    a: torch.Tensor | int | None,
    b: torch.Tensor | int | None,
    mode: FakeTensorMode,
):
    from torch.fx.experimental.symbolic_shapes import (
        has_free_unbacked_symbols,
        SymIntEqByExpr,
    )

    if a is None or b is None:
        if not (a is None and b is None):
            raise AssertionError(f"expected both a and b to be None, got a={a}, b={b}")
        return None

    def min_max(s0, s1):
        def _bound(s0, lower_bound: bool):
            if isinstance(s0, int):
                return s0
            r = mode.shape_env.var_to_range.get(  # type: ignore[union-attr]
                s0.node.expr,
                torch.utils._sympy.value_ranges.ValueRanges.unknown(),
            )
            return r.lower if lower_bound else r.upper

        return min(_bound(s0, True), _bound(s1, True)), max(
            _bound(s0, False), _bound(s1, False)
        )

    if type(a) is int and type(b) is int:
        if a == b:
            return a
        if mode.shape_env is None:
            raise AssertionError("mode.shape_env is None")
        merged_out = mode.shape_env.create_unbacked_symint()
        mode.shape_env.constrain_symbol_range(merged_out.node.expr, *min_max(a, b))
        return merged_out

    if not (type(a) is FakeTensor and type(b) is FakeTensor):
        raise AssertionError(
            f"expected both a and b to be FakeTensor, got a={type(a)}, b={type(b)}"
        )

    # Note: we don't check size, stride because
    # they'll be merged with unbacked symints if they differ.
    _meta_to_check = {
        "dtype",
        "device",
        "layout",
        "dim",
        "is_quantized",
        "is_conj",
        "is_sparse",
        "storage_offset",
    }
    check_tensor_meta_match(
        a,
        b,
        tuple(_meta_to_check),
        msg_prefix="When merging two branches' output in torch.cond, ",
    )
    # NYI
    if a.is_quantized or b.is_quantized:
        raise AssertionError("quantized tensors not yet implemented")
    if a.is_sparse or b.is_sparse:
        raise AssertionError("sparse tensors not yet implemented")
    if a.is_conj() or b.is_conj():
        raise AssertionError("conjugate tensors not yet implemented")

    """
    Step 1: create unbacked symints for sizes that are different
    along the same axis. For example:
        a.size is [s0, 4, s0, 5, 4, 5]
        b.size is [s1, 4, s2, 8, 4, 7]
        merged_size will be [u0, 4, u1, u2, 4, u3], where
        u0 has range [min(s0, s1), max(s0, s1)]
        u1 has range [min(s0, s2), max(s0, s2)]
        u2 has range [5, 8]
        u3 has range [5, 7]
    """
    merged_size: list[int | torch.SymInt] = []

    def _has_unbacked_symbols(s: int | torch.SymInt) -> bool:
        if isinstance(s, int):
            return False
        else:
            return has_free_unbacked_symbols(s.node.expr)

    for s0, s1 in zip(a.size(), b.size()):
        # If there are unbacked symbols leaked out of true_branch or false_branch
        # we need to merge them with a new unbacked symbol and track in parent graph.
        if (
            not _has_unbacked_symbols(s0)
            and not _has_unbacked_symbols(s1)
            and SymIntEqByExpr(s0) == SymIntEqByExpr(s1)
        ):
            merged_size.append(s0)
        else:
            if mode.shape_env is None:
                raise AssertionError("mode.shape_env is None")
            new_size = mode.shape_env.create_unbacked_symint()
            mode.shape_env.constrain_symbol_range(new_size.node.expr, *min_max(s0, s1))
            merged_size.append(new_size)

    """
    This follows the logic in symbolic_shapes._compute_symbolic_stride
    Step 2: Since tensor stride is an accumulative multiplication of the sizes, which is a permutated
        (due to view ops) non-descending sequence.

        Case 1: No size is 1. In this case, strides have unique values.
            For example, suppose we have a tensor with:
            size [3, 4, 3, 5, 4, 5],
            stride (1200, 300, 1, 12, 3, 60),
            merged_size [u0, u1, u2, u3, u4, u5].

            We visit the strides in ascending order: 1, 3, 12, 60, 300, 1200. In each step, we check whether
            the current stride is bounded or not and bound next stride by setting.
                stride_expr[next_stride] = current_stride_expr * current_size_expr
            1st round:
                current_stride is 1, current_size is 3, so next_stride is 1 * 3 = 3,
                current_stride_expr is set to 1, current_size_expr is u2, so stride_expr[3] is therefore 1 * u2 = u2
            2nd round:
                current_stride is 3, current_size is 4, so next_stride is 3 * 4 = 12,
                current_stride_expr is stride_expr[3] i.e. u2, current_size_expr is u4, so stride_expr[12] = u2 * u4
                ...

        Case 2: At least one dimension has size 1, which can produce duplicates in strides.
            In this case, theoretically, we cannot uniquely determine the expr of strides because
            the accessing stride_expr with same key in different order causes the final stride expression
            to be different.

            Suppose we have:
                size: (3, 1)
                stride: (1, 1)
                merged_size: (u0, u1)

            The stride expr could either be (u1, 1) or (1, u0) depending on whether we start with u1 or u0.
            For this reason, we try to break tie by sorting via descending index so we always get (u1, 1).

            Note that backend might optimize the strides anyway so this is usually not a problem as long
            as two branches matches. See relevant discussions in https://github.com/pytorch/pytorch/issues/142024.

        Case 3: Dim has 0 stride. 0 stride doesn't participate in the accumulative multiplication of
            sizes. So they're always treated as constant even if their corresponding size is turned into unbacked symint.

            Suppose we have:
                size: (3, 3)
                stride: (0, 1)
                merged_size: (u0, u1)

            The merged stride would be (0, 1)
    """

    def _bound_stride(
        a_ex_size: torch.Size,
        b_ex_size: torch.Size,
        a_ex_stride: tuple[int, ...],
        b_ex_stride: tuple[int, ...],
        merged_size: list[int | torch.SymInt],
    ) -> list[int | torch.SymInt]:
        from torch._inductor.ir import get_stride_order

        a_sorted_stride_idx = get_stride_order(a_ex_stride, mode.shape_env)
        b_sorted_stride_idx = get_stride_order(b_ex_stride, mode.shape_env)

        a_stride_li: list[tuple[int | torch.SymInt, int] | None] = [None] * len(
            a_ex_stride
        )
        b_stride_li: list[tuple[int | torch.SymInt, int] | None] = [None] * len(
            b_ex_stride
        )
        for i, idx in enumerate(a_sorted_stride_idx):
            a_stride_li[idx] = (a_ex_stride[i], -i)
        for i, idx in enumerate(b_sorted_stride_idx):
            b_stride_li[idx] = (b_ex_stride[i], -i)

        for a_pair, b_pair in zip(a_stride_li, b_stride_li):
            if a_pair is None or b_pair is None:
                raise AssertionError(
                    f"expected a_pair and b_pair to be non-None, got a_pair={a_pair}, b_pair={b_pair}"
                )
            _, a_idx = a_pair
            _, b_idx = b_pair

            if a_idx != b_idx:
                raise RuntimeError(
                    f"The sorted order of strides of the two branches' output doesn't match."
                    f"this indicates the contiguousness of the two branches are different. "
                    f"True branch has stride {a_ex_stride} but false branch has stride {b_ex_stride}."
                    f"Consider using contiguous() to make the two branches have the same contiguousness."
                )

        def _maybe_expr(s: int | torch.SymInt):
            if isinstance(s, int):
                return s
            return s.node.expr

        a_stride_expr: dict[Any, int | torch.SymInt] = {}
        b_stride_expr: dict[Any, int | torch.SymInt] = {}
        merged_strides: list[int | torch.SymInt] = [None] * len(a_ex_stride)  # type: ignore[list-item]
        for a_pair, b_pair in zip(a_stride_li, b_stride_li):
            if a_pair is None or b_pair is None:
                raise AssertionError(
                    f"expected a_pair and b_pair to be non-None, got a_pair={a_pair}, b_pair={b_pair}"
                )
            a_val, neg_i = a_pair
            b_val, _ = b_pair

            i = -neg_i
            if a_val == 0:
                if b_val != 0:
                    raise AssertionError(
                        f"expected b_val == 0 when a_val == 0, got a_val={a_val}, b_val={b_val}"
                    )
                merged_strides[i] = 0
                continue

            if _maybe_expr(a_val) in a_stride_expr:
                a_expr = a_stride_expr[_maybe_expr(a_val)]
                if b_stride_expr[_maybe_expr(b_val)] != a_expr:
                    raise AssertionError(
                        f"a_stride_expr:{a_stride_expr}, b_stride_expr:{b_stride_expr}"
                    )
                merged_strides[i] = a_expr
            else:
                if a_val == 1:
                    if b_val != 1:
                        raise AssertionError(
                            f"expected b_val == 1 when a_val == 1, got b_val={b_val}"
                        )
                    a_stride_expr[_maybe_expr(a_val)] = 1
                    b_stride_expr[_maybe_expr(b_val)] = 1
                    merged_strides[i] = 1
                else:
                    # If we cannot find the expr of a_val in a_stride_expr, it means
                    # the strides is not a simple accumulative multiplication of sizes.
                    # In this case, we cannot determine the expr of strides from the new
                    # shapes so we error out and hint users to call contiguous().
                    raise RuntimeError(
                        f"It seems one of cond's output stride is not a simple accumulative multiplication of sizes. "
                        f"This could be because cond returns a slice of a tensor, which is not dense in memory. "
                        f"True branch has size {a_ex_size}, stride {a_ex_stride} and false branch has size {b_ex_size} "
                        f"stride {b_ex_stride}. Hint: can call t.contiguous(). "
                    )
            nxt_merged_stride_expr = merged_strides[i] * merged_size[i]
            a_stride_expr[_maybe_expr(a_val * a_ex_size[i])] = nxt_merged_stride_expr
            b_stride_expr[_maybe_expr(b_val * b_ex_size[i])] = nxt_merged_stride_expr
        return merged_strides

    merged_stride: list[int | torch.SymInt] = _bound_stride(
        a.size(), b.size(), a.stride(), b.stride(), merged_size
    )

    with mode:
        return torch.empty_strided(
            merged_size, merged_stride, dtype=a.dtype, device=a.device
        )