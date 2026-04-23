def test_foreach_copy_with_multi_device_inputs(self, device, dtype, op):
        foreach_copy_ = op.inplace_variant
        copy_ = op.ref_inplace
        for non_blocking in (False, True):
            for sample in op.sample_inputs(
                device, dtype, noncontiguous=False, allow_higher_dtype_scalars=True
            ):
                with torch.no_grad():
                    ref_input = [t.detach().clone() for t in sample.input]
                foreach_copy_(sample.input, sample.args[0], non_blocking)
                for t, s in zip(ref_input, sample.args[0]):
                    copy_(t, s, non_blocking)
                self.assertEqual(sample.input, ref_input)
                if torch.cuda.device_count() > 1:
                    device = torch.device("cuda", 1)
                    rhs_tensors = [t.to(device) for t in sample.args[0]]
                    foreach_copy_(sample.input, rhs_tensors, non_blocking)
                    for t, s in zip(ref_input, rhs_tensors):
                        copy_(t, s, non_blocking)
                    self.assertEqual(ref_input, sample.input)