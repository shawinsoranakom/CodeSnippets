def test_meta_outplace(self, device, dtype, op):
        if "_scaled_mm" in op.name:
            raise unittest.SkipTest("_scaled_mm dose not support meta device")
        skip_op_names = (
            "fft.ihfft",
            "fft.ihfft2",
            "linalg.lu_solve",
        )
        if TEST_WITH_TORCHDYNAMO and op.name in skip_op_names:
            raise unittest.SkipTest("flaky")
        # run the OpInfo sample inputs, cross-referencing them with the
        # meta implementation and check the results are the same.  All
        # the heavy lifting happens in MetaCrossRefFunctionMode
        func = op.get_op()
        samples = op.sample_inputs(device, dtype, requires_grad=False)
        for sample_input in samples:
            args = [sample_input.input] + list(sample_input.args)
            kwargs = sample_input.kwargs
            with MetaCrossRefFunctionMode(self, dtype=dtype, device=device, inplace=False):
                expected = func(*args, **kwargs)
                if isinstance(expected, torch.Tensor) and op.supports_out:
                    func(*args, **kwargs, out=expected)

            # Special test for functions taking "device" kwarg
            # The crossref tests that replacing the device with "meta" works
            # This part makes sure that *_like functions work well with a "meta"
            # Tensor and their original device argument.
            if "device" in kwargs and "_like" in op.name:
                with torch.random.fork_rng():
                    torch.manual_seed(123)
                    ref = func(*args, **kwargs)

                # *_like functions take a Tensor as first argument
                if not isinstance(args[0], torch.Tensor):
                    raise AssertionError(f"expected args[0] to be Tensor, got {type(args[0])}")
                with torch.random.fork_rng():
                    torch.manual_seed(123)
                    args[0] = args[0].to(device="meta")
                    meta = func(*args, **kwargs)

                # empty_like is not deterministic
                if op.name != "empty_like":
                    self.assertEqual(ref, meta)