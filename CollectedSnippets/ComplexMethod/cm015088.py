def test_foreach_copy_with_different_device_inputs(self, device, dtype, op):
        if dtype in (torch.complex128, torch.complex64):
            self.skipTest("Complex dtype not supported")
        # check foreach_copy when self and src tensorList have different device
        foreach_copy = op.method_variant
        copy_ = op.ref_inplace

        def fn(self_tensor, src_tensor, non_blocking):
            return foreach_copy(self_tensor, src_tensor, non_blocking)

        fn = torch.compile(fn)
        for non_blocking in (False,):
            for sample in op.sample_inputs(
                device, dtype, noncontiguous=False, allow_higher_dtype_scalars=True
            ):
                with torch.no_grad():
                    ref_input = [t.detach().clone() for t in sample.input]
                    ref_input_cpu = [t.detach().clone().to("cpu") for t in sample.input]
                    rhs_tensors = [t.detach().clone().to("cpu") for t in sample.args[0]]
                    self_tensors = [t.detach().clone().to("cpu") for t in sample.input]

                output1 = fn(sample.input, rhs_tensors, non_blocking)
                for t, s in zip(ref_input, rhs_tensors):
                    copy_(t, s, non_blocking)
                self.assertEqual(output1, ref_input)

                output2 = fn(self_tensors, sample.args[0], non_blocking)
                for t, s in zip(ref_input_cpu, sample.args[0]):
                    copy_(t, s, non_blocking)
                self.assertEqual(output2, ref_input_cpu)