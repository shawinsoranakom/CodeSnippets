def adjust_kernel_inputs(
        self, kernel_inputs: KernelInputs, op_name: str
    ) -> KernelInputs:
        """
        for scaled_mm, we need to unsqueeze scale tensors, and bias
        """
        assert isinstance(kernel_inputs, MMKernelInputs), (
            "Expect MMKernelInputs for scaled MM"
        )
        inputs = super().adjust_kernel_inputs(kernel_inputs, op_name)
        nodes = inputs.nodes()
        mat_a, mat_b, scale_a, scale_b, *bias = nodes
        bias = bias[0] if bias else None
        # Prepare triton input nodes and create kernel_inputs at the top
        from ..lowering import lowerings as L

        aten = torch.ops.aten
        if bias and len(mat_b.get_size()) == len(bias.get_size()) + 1:
            # Need to unsqueeze bias from [N] -> [1, N]
            bias = L[aten.unsqueeze](bias, 0)

        if len(scale_a.get_size()) == 0 or len(scale_b.get_size()) == 0:
            assert len(scale_a.get_size()) == len(scale_b.get_size())
            # Need to unsqueeze scale from [] -> [1, 1]
            scale_a = L[aten.unsqueeze](L[aten.unsqueeze](scale_a, 0), 1)
            scale_b = L[aten.unsqueeze](L[aten.unsqueeze](scale_b, 0), 1)
        nodes = [mat_a, mat_b, scale_a, scale_b]
        if bias:
            nodes.append(bias)
        return MMKernelInputs(
            nodes,
            mat1_idx=kernel_inputs._mat1_idx,
            mat2_idx=kernel_inputs._mat2_idx,
            out_dtype=kernel_inputs._out_dtype,
        )