def _apply_constraint_inner(idx, arg, meta_val, meta_stride_expr, stride_order):
        if not (meta_val.is_cuda or meta_val.is_xpu):
            return ir.ExternKernel.require_stride_order(arg, stride_order)

        # This is the minimum alignment required by SDPA kernels for attention_bias.
        # This value can be found in pytorch/aten/src/ATen/native/transformers/attention.cpp preprocess_mask
        ALIGNMENT = 8

        # effn_attn_fwd does requires dense last dim, not just alignment
        effn_attn_fwd_bias = (
            fx_node.target
            == torch.ops.aten._scaled_dot_product_efficient_attention.default
            and idx == 3
        )

        assert isinstance(arg, TensorBox)
        if len(arg.get_size()) not in (3, 4):
            return arg

        is_aligned_tensor = ir.is_aligned_realized_tensor(arg, ALIGNMENT)
        if is_aligned_tensor:
            return ir.try_match_insignificant_strides(
                ir.ExternKernel.realize_input(arg), meta_stride_expr
            )

        if (
            isinstance(arg, IRNode)
            and arg.maybe_get_stride() is not None
            and is_aligned_tensor
        ):
            return ir.try_match_insignificant_strides(
                ir.ExternKernel.realize_input(arg), meta_stride_expr
            )

        if effn_attn_fwd_bias:
            out_size = list(arg.get_size())

            expanded_dims = []
            # We require a dense last dimension, but the other strides
            # can be expanded, which results in a smaller tensor
            maybe_stride = arg.maybe_get_stride()
            for i in range(len(arg.get_size()) - 1):
                if V.graph.sizevars.statically_known_equals(meta_stride_expr[i], 0) or (
                    maybe_stride is not None
                    and V.graph.sizevars.statically_known_equals(maybe_stride[i], 0)
                ):
                    expanded_dims.append(i)

            # Now, pad strides to alignment
            out_strides = [-1] * len(out_size)
            out_strides[-1] = 1
            stride = 1
            for i in range(len(out_size) - 2, -1, -1):
                if out_strides[i + 1] != 0:
                    stride = stride * out_size[i + 1]

                # the expanded dims still need to be aligned, if they are,
                # we can make them expanded by setting the stride equal to 0
                if i in expanded_dims:
                    if V.graph.sizevars.statically_known_equals(
                        Mod(out_strides[i + 1], ALIGNMENT), 0
                    ):
                        out_strides[i] = 0
                        continue

                if not V.graph.sizevars.statically_known_equals(
                    Mod(stride, ALIGNMENT), 0
                ):
                    stride = ceildiv(stride, ALIGNMENT) * ALIGNMENT

                out_strides[i] = stride

            return ir.ExternKernel.require_exact_strides(arg, out_strides)

        if is_aligned_tensor:
            return ir.try_match_insignificant_strides(
                ir.ExternKernel.realize_input(arg), meta_stride_expr
            )

        if (
            isinstance(arg, IRNode)
            and arg.maybe_get_stride() is not None
            and is_aligned_tensor
        ):
            return ir.try_match_insignificant_strides(
                ir.ExternKernel.realize_input(arg), meta_stride_expr
            )

        def is_aligned(x):
            return V.graph.sizevars.guard_or_false(
                sympy.Eq(Mod(x.get_size()[-1], ALIGNMENT), 0)
            )

        if isinstance(arg.data, ir.BaseView):
            if not is_aligned(arg):
                if is_aligned(arg.unwrap_view()):
                    return ir.try_match_insignificant_strides(
                        ir.ExternKernel.realize_input(arg), meta_stride_expr
                    )

        return ir.ExternKernel.require_stride_order(arg, stride_order)