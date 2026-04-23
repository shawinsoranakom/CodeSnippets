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