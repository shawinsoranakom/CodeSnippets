def fix_op_layout(
        self,
        op: "cutlass_library.gemm_op.GemmOperation",  # type: ignore[name-defined] # noqa: F821
        X: Buffer,
        W: Buffer,
        Bias: Buffer | None,
        Y: Buffer | ReinterpretView,
    ) -> "cutlass_library.gemm_op.GemmOperation":  # type: ignore[name-defined]  # noqa: F821
        # This is a workaround to deal with cases where the input layouts have changed
        # between autotuning and rendering. This happens if the inputs layout
        # are FlexibleLayout instances. In this case, we need to update the
        # op's input layouts. It is a hack, because now the op
        # we benchmarked is not the same as the op we render,
        # but there is no simple way to fix this in the autotuner, since that would
        # potentially disable other optimizations.
        a_layout = X.get_layout()
        b_layout = W.get_layout()
        c_layout = Bias.get_layout() if Bias is not None else None

        d_layout = copy.deepcopy(Y.get_layout())
        match_list = [
            CUTLASSGemmTemplate.layout_match(buf.get_layout(), op_layout)
            for buf, op_layout in zip(
                (X, W, Bias, Y),
                (op.A.layout, op.B.layout, op.C.layout, op.D.layout),
            )
            if buf is not None
        ]
        all_match = all(match_list)
        if all_match:
            return op
        log.warning(
            f"Cutlass GEMM Layout change: Input and/or output layouts have changed between autotuning/retuning and call to render on {self}. Applying workaround. This can lead to suboptimal performance. Match List: {match_list}"  # noqa: G004
        )
        new_op = copy.deepcopy(op)

        if a_layout is not None:
            new_op.A.layout = CUTLASSGemmTemplate.cutlass_layout(a_layout)
        if b_layout is not None:
            new_op.B.layout = CUTLASSGemmTemplate.cutlass_layout(b_layout)
        if c_layout is not None:
            new_op.C.layout = CUTLASSGemmTemplate.cutlass_layout(c_layout)
            new_op.C.element = cutlass_utils.torch_dtype_to_cutlass_type(c_layout.dtype)
        if d_layout is not None:
            new_op.D.layout = CUTLASSGemmTemplate.cutlass_layout(d_layout)
        return new_op