def pack_vnni_weight(cls, W, micro_gemm, new_size):
        # WOQ INT4 weights are reordered in microkernel so do not pack them here
        should_pack = (
            micro_gemm.get_b_layout() != LayoutType.NORMAL
            and not micro_gemm.is_woq_int4()
        )

        # These are separated into two methods to allow subclasses to override them separately
        if isinstance(W, ir.IRNode):
            if isinstance(W, ir.Buffer) and W.get_name() in V.graph.constants:
                return W
            k = new_size[-2]
            if not isinstance(W, ir.TensorBox):
                W = ir.TensorBox(W)
            if should_pack:
                permute_dims = list(range(len(new_size) + 1))
                permute_dims[-1], permute_dims[-2] = permute_dims[-2], permute_dims[-1]
                vnni_size = 4 if micro_gemm.get_b_layout() == LayoutType.VNNI4 else 2
                vnni_view_size = list(new_size)
                vnni_view_size[-2] = k // vnni_size
                vnni_view_size.insert(-1, vnni_size)
                W = L.view(
                    L.permute(L.view(W, vnni_view_size), permute_dims),
                    new_size,
                )
            W = ir.ExternKernel.realize_input(W)
            W = ir.ExternKernel.require_contiguous(W)
            return W
        else:
            k = new_size[-2]
            # Apply VNNI packing to the weight tensor
            if should_pack:
                # TODO: Move VNNI weight packing for non-constant tensors into the template,
                # to improve cache locality and avoid full-tensor copy.
                layout_str = (
                    "VNNI4"
                    if micro_gemm.get_b_layout() == LayoutType.VNNI4
                    else "VNNI2"
                )
                assert micro_gemm.get_b_layout() in [
                    LayoutType.VNNI2,
                    LayoutType.VNNI4,
                ], f"We only support {layout_str} for now"
                vnni_size = 4 if micro_gemm.get_b_layout() == LayoutType.VNNI4 else 2
                assert k % vnni_size == 0, (
                    f"k should be divisible by vnni_size for {layout_str} layout"
                )
                vnni_view_size = list(new_size)
                vnni_view_size[-2] = k // vnni_size
                vnni_view_size.insert(-1, vnni_size)
                W = W.view(vnni_view_size).transpose(-1, -2).contiguous().view(new_size)
            # normalize stride to be "contiguous_strides" per size
            # this avoids the problems in L.view during template codegen
            new_stride = [1]
            for sz in reversed(W.shape[1:]):
                new_stride.insert(0, new_stride[0] * sz)
            W = W.as_strided(W.shape, new_stride)
            return W