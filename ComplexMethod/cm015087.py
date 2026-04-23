def test_foreach_copy_with_mixed_dtypes_within_tensor(self, device, dtype, op):
        foreach_copy_ = ForeachFuncWrapper(op.inplace_variant)

        for sample in op.sample_inputs(
            device, dtype, noncontiguous=False, allow_higher_dtype_scalars=True
        ):
            if len(sample.input) < 2:
                continue

            dtypes = [torch.float32, torch.bfloat16, torch.float16]
            uniform_tensors = [t.clone() for t in sample.input]
            mixed_tensors = [
                t.clone().to(dtype)
                for t, dtype in zip(sample.input, itertools.cycle(dtypes))
            ]

            uniform_dst = [torch.empty_like(t) for t in uniform_tensors]
            out = foreach_copy_(
                (uniform_dst, mixed_tensors), is_cuda=True, expect_fastpath=False
            )
            out_ref = [
                torch.empty_like(t1).copy_(t2)
                for t1, t2 in zip(uniform_tensors, mixed_tensors)
            ]
            for t, ref_t in zip(out, out_ref):
                self.assertTrue(torch.equal(t, ref_t))

            mixed_dst = [torch.empty_like(t) for t in mixed_tensors]
            out = foreach_copy_(
                (mixed_dst, uniform_tensors), is_cuda=True, expect_fastpath=False
            )
            out_ref = [
                torch.empty_like(t1).copy_(t2)
                for t1, t2 in zip(mixed_tensors, uniform_tensors)
            ]
            for t, ref_t in zip(out, out_ref):
                self.assertTrue(torch.equal(t, ref_t))