def _compute_symbolic_stride(
        self,
        source: Source,
        size: Sequence[sympy.Expr],
        ex_size: Sequence[IntLikeType],
        ex_stride: Sequence[IntLikeType],
        dynamic_strides: Sequence[DimDynamic],
        constraint_strides: Sequence[
            StrictMinMaxConstraint | RelaxedUnspecConstraint | None
        ],
        are_sizes_static: bool,
        symbolic_context: SymbolicContext,
    ) -> list[sympy.Expr]:
        from torch._dynamo.source import TensorProperty, TensorPropertySource

        stride: list[sympy.Expr | None] = [None] * len(size)
        candidates: dict[IntLikeType, sympy.Expr] = {}

        # iterate over unbound strides in val ascending order with
        # index descending as a tie breaker since for cases like
        # [(1, 1), (1, 0)], we want to fill in the right most
        # stride first.
        val_list = [(val, -i) for i, val in enumerate(ex_stride)]
        val_list.sort(key=_nested_int_aware_sort)

        for val, neg_i in val_list:
            i = -neg_i
            contiguous_stride = (
                i != len(ex_stride) - 1
                and ex_stride[i] == ex_size[i + 1] * ex_stride[i + 1]
            )
            if val in (0, 1) and not contiguous_stride:
                out_stride = sympy.Integer(val)
            else:
                dynamic_stride = dynamic_strides[i]
                if dynamic_stride == DimDynamic.INFER_STRIDE and val in candidates:
                    # Set stride to a candidate only for DimDynamic.INFER_STRIDE
                    out_stride = candidates[val]
                else:
                    # Set INFER_STRIDE to STATIC or DUCK depending on sizes
                    dyn_stride = dynamic_stride
                    if dynamic_stride == DimDynamic.INFER_STRIDE:
                        dyn_stride = (
                            DimDynamic.STATIC if are_sizes_static else DimDynamic.DUCK
                        )
                    out_stride = self.create_symbol(
                        val,
                        TensorPropertySource(source, TensorProperty.STRIDE, i),
                        dynamic_dim=dyn_stride,
                        constraint_dim=constraint_strides[i],
                        symbolic_context=symbolic_context,
                    )
            stride[i] = out_stride
            candidates[ex_size[i] * val] = size[i] * out_stride

        if not all(x is not None for x in stride):
            raise AssertionError("All stride elements must be non-None")
        return stride