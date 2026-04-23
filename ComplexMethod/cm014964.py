def _run_dispatch_meta_test(self, device, dtype, op, symbolic_meta, inplace, all_stride_variants=False):
        if "_scaled_mm" in op.name:
            raise unittest.SkipTest("_scaled_mm dose not support meta device")
        if inplace:
            func = op.get_inplace()
            if not func:
                self.skipTest("No inplace variable for this op")
            if op.promotes_int_to_float and not dtype.is_floating_point:
                self.skipTest("Op promotes to float, which is impossible for inplace with non-float input")
        else:
            func = op.get_op()

        if func in meta_dispatch_early_skips:
            self.skipTest("Function is in dispatch early skips")

        if inplace:
            func = self._get_safe_inplace(func)

        samples = op.sample_inputs(device, dtype, requires_grad=False)
        for sample_input in samples:
            if inplace and sample_input.broadcasts_input:
                continue

            sample_args = [sample_input.input] + list(sample_input.args)
            kwargs = sample_input.kwargs

            if all_stride_variants and sum(isinstance(arg, torch.Tensor) for arg in sample_args) <= 5:
                # test inputs <= 5 tensors to avoid combinatorial explosion
                strided_args = get_strided_args(sample_args)
            else:
                strided_args = [sample_args]

            for args in strided_args:
                with MetaCrossRefDispatchMode.push(
                    self, dtype=dtype, device=device,
                    symbolic_meta=symbolic_meta, inplace=inplace,
                     supports_out=op.supports_out):
                    expected = func(*args, **kwargs)

                    if not inplace and isinstance(expected, torch.Tensor) and op.supports_out:
                        func(*args, **kwargs, out=expected)