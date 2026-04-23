def check_inplace_view(func, input, rs, input_size, input_strides):
    if func is None:
        return
    # TODO: extend this test to test ops with multiple outputs and ops like native_batch_norm(_legit).out
    # which mutate not necessarily the first input.
    if isinstance(rs, torch.Tensor) and rs is input:
        unequal_size = rs.size() != input_size
        unequal_strides = rs.stride() != input_strides
        # resize_ should probably have inplace_view tag. Not adding the tag since it
        # breaks some codegen logic
        if unequal_size or unequal_strides:
            if isinstance(func, torch._ops.OpOverloadPacket):
                func = func.default
            # Reference: https://github.com/pytorch/pytorch/issues/78759
            if func is not torch.ops.aten.resize_.default:
                # TODO: use self.assertIn when we have separate tests for each tag
                if torch.Tag.inplace_view not in func.tags:
                    raise AssertionError(f"expected inplace_view tag in {func.tags}")