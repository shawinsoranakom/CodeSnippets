def test_foreach_copy_with_multi_dtypes(self, device, dtype, op):
        # check (a) multi_tensor_apply is called and (b) numerical parity with for-loop and Tensor.copy_
        foreach_copy_ = ForeachFuncWrapper(op.inplace_variant)

        for sample in op.sample_inputs(
            device, dtype, noncontiguous=False, allow_higher_dtype_scalars=True
        ):
            for src_dtype in floating_types_and(torch.half, torch.bfloat16):
                if src_dtype == dtype:
                    continue
                self_tensors = [t.clone() for t in sample.input]
                src_tensors = [t.to(src_dtype) for t in self_tensors]
                out = foreach_copy_(
                    (self_tensors, src_tensors), is_cuda=True, expect_fastpath=True
                )
                ref_out = [
                    torch.empty_like(t).copy_(s)
                    for t, s in zip(self_tensors, src_tensors)
                ]
                for t, ref_t in zip(out, ref_out):
                    self.assertTrue(torch.equal(t, ref_t))