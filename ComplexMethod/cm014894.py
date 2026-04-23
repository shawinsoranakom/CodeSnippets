def test_output_match(self, device, dtype, op):
        self.assertEqual(device, "mps:0")
        include_conjugated_inputs = dtype.is_complex and op.test_conjugated_samples

        for mps_sample in op.sample_inputs(
                device,
                dtype,
                requires_grad=(dtype.is_floating_point or dtype.is_complex),
                include_conjugated_inputs=include_conjugated_inputs,
                set_seed=True):

            opt_dtype = None

            if op.name == "histc" and not dtype.is_floating_point and not dtype.is_complex:
                opt_dtype = dtype

            mps_out, cpu_out, cpu_sample = self._run_op(op, mps_sample, opt_dtype)

            atol, rtol = self._compute_tolerances(op, dtype)
            if (op.name == "nn.functional.interpolate" and dtype == torch.uint8 and
               mps_sample.kwargs.get("mode") == "bilinear" and
               mps_sample.kwargs.get("recompute_scale_factor") is True and
               mps_sample.kwargs.get("scale_factor") == 1.7):
                # For 1/3, 2/3 scale factors results will not match CPU ones
                # As MPS compute scales in floats, but CPU always used doubles, which results
                # in slight numerical differences
                atol, rtol = 1, 0

            if (op.name in ["_upsample_bilinear2d_aa", "_upsample_bicubic2d_aa"]
               and mps_sample.kwargs.get("scale_factors") == [1.7, 0.9]):
                # Similar to the above, float vs double precision aresults in slight error
                atol, rtol = 2e-5, 2e-6

            if op.name == "kthvalue":
                self.assertEqual(cpu_out[0], mps_out[0], atol=atol, rtol=rtol)
                # kthvalue is non-deterministic if input has repeated values
                dim = mps_sample.args[1] if len(mps_sample.args) > 1 else -1
                keep_dim = mps_sample.args[2] if len(mps_sample.args) > 2 else False
                values = torch.gather(mps_sample.input, dim, mps_out[1] if keep_dim else mps_out[1].unsqueeze(dim))
                self.assertEqual(values if keep_dim else values.squeeze(dim), mps_out[0])
                continue

            self.assertEqual(cpu_out, mps_out, atol=atol, rtol=rtol)