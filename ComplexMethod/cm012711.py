def prep_weight(
        cls,
        inputs,
        layout: ir.Layout,
        micro_gemm: CppMicroGemm,
        should_block_weight: bool,
        use_int8_fast_compensation_path: bool = False,
        skip_int8_compensation: bool = False,
    ):
        """
        NOTE Weight prep consists of 2 separate steps:
        1. Blocking the weight tensor into a 3D shape: [n//block_n, k, block_n]
           This is always done if the weight tensor is constant, i.e. for all GEMM and some BMM.
           For BMM, we also block non-contiguous weight tensors, since they would be reshaped anyway.
           This assumes that blocked, contiguous weights will be more efficient for the GEMM kernel,
           and is worth the overhead of reshape and blocking.

           This blocking includes additional padding, when n is not a multiple of block_n.
           This padding allows a more efficient microkernel implementation. For BMM, this is only done
           if reshape would happen anyway, i.e.  if the weight tensor is constant, is not contiguous,
           or is using AMX VNNI layout.
        2. Packing the weight tensor into a VNNI-friendly shape. For constant input,
           this is done at the same time as the weight blocking.

        At compile time, the constant weight tensors are blocked and packed. For non-constant tensors (e.g. BMM)
        which will be blocked (non-contiguous or VNNI-layout tensors), the weight tensor is blocked and packed at runtime.

        CppBmmTemplate overrides the methods get_padded_size, and block_weight in order to accommodate
        an additional dimension for the batch size and to determine if the weight tensor should be blocked.
        """
        W = inputs[1]
        new_inputs = list(inputs)
        if cls.is_woq_int4():
            assert (
                len(W.get_size()) == 2
                if isinstance(W, ir.IRNode)
                else len(W.shape) == 2
            )
            n, k = W.get_size() if isinstance(W, ir.IRNode) else W.shape
        else:
            k, n = W.get_size()[-2:] if isinstance(W, ir.IRNode) else W.shape[-2:]
        _, block_n, _ = micro_gemm.register_blocking
        new_size, padded_n = cls.get_padded_size(n, block_n, k, should_block_weight)
        padding = padded_n - n

        if should_block_weight and not cls.is_woq_int4():
            blocked_w = cls.block_weight(W, new_size, padding)
            new_inputs[1] = cls.pack_vnni_weight(blocked_w, micro_gemm, new_size)
        elif should_block_weight:
            assert cls.is_woq_int4()
            new_inputs[1] = cls.block_weight(W, new_size, padding)
        elif isinstance(W, ir.IRNode):
            # Require W layout to be fixed & contiguous, happens inplace.
            ir.ExternKernel.require_contiguous(W)
            new_inputs[1] = cls._maybe_remove_storage_offset(W)

        if not skip_int8_compensation and _is_int8_gemm(new_inputs):
            BCompensate = None
            x_w_scale = None

            def _get_compensation_node(W, use_int8_fast_compensation_path):
                BCompensate = V.graph.add_tensor_constant(
                    V.graph.constants[W.get_name() + "_BMatrixCompens"],
                    W.get_name() + "_BMatrixCompens",
                )
                x_w_scale = None
                if use_int8_fast_compensation_path:
                    x_w_scale = V.graph.add_tensor_constant(
                        V.graph.constants[W.get_name() + "_x_w_compens"],
                        W.get_name() + "_x_w_compens",
                    )
                return BCompensate, x_w_scale

            if use_int8_fast_compensation_path:
                # new_inputs has been reordered: [x, w, optional[bias], x_scale, x_zp, w_scale, w_zp]
                x_scale = new_inputs[-4]
                x_zp = new_inputs[-3]
                w_scale = new_inputs[-2]
                if isinstance(W, ir.IRNode):
                    BCompensate, x_w_scale = _get_compensation_node(
                        W, use_int8_fast_compensation_path
                    )
                else:
                    # Use the original W, not the blocked_w in new_inputs[1] to calculate BCompensate
                    BCompensate = torch.sum(W.to_dense().to(torch.float), dim=0)  # type: ignore[assignment]
                    assert all(
                        isinstance(item, torch.Tensor)
                        for item in (x_scale, x_zp, w_scale)
                    )
                    BCompensate = BCompensate * x_scale * w_scale * x_zp
                    x_w_scale = x_scale * w_scale
                new_inputs.append(BCompensate)
                new_inputs.append(x_w_scale)
            else:
                if isinstance(W, ir.IRNode):
                    BCompensate, _ = _get_compensation_node(
                        W, use_int8_fast_compensation_path
                    )
                else:
                    # Use the original W, not the blocked_w in new_inputs[1] to calculate BCompensate
                    BCompensate = torch.sum(W.to_dense().to(torch.float), dim=0)  # type: ignore[assignment]
                new_inputs.append(BCompensate)
        return new_inputs, layout