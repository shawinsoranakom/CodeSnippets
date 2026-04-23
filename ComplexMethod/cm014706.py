def test_mixed_device_dtype(self, device, dtype, optim_info, impl):
        """
        Similar in essence to _test_derived_optimizers above. The main difference is that
        _test_derived_optimizers uses model parameters whereas we randomly pass in
        parameters of different dtypes and devices here. We need multiple GPUs (vs just a
        CPU and GPU) because fused adam only works on GPUs. (Thus we only run the tests
        that call into this helper when TEST_MULTIGPU.)
        """
        if impl not in ("foreach", "fused"):
            raise AssertionError(f"impl must be 'foreach' or 'fused', got {impl!r}")
        if impl == "foreach" and "foreach" not in optim_info.supported_impls:
            return unittest.skip(
                f"foreach not supported for {optim_info.optim_cls.__name__}"
            )
        elif impl == "fused" and "cuda" not in optim_info.supports_fused_on:
            return unittest.skip(
                f"fused not supported for {optim_info.optim_cls.__name__} on cuda"
            )

        params = [
            torch.rand(2, 3, dtype=torch.float64, device="cuda:0", requires_grad=True),
            torch.rand(2, 3, dtype=torch.float32, device="cuda:0", requires_grad=True),
            torch.rand(2, 3, dtype=torch.float16, device="cuda:0", requires_grad=True),
            torch.rand(2, 3, dtype=torch.bfloat16, device="cuda:0", requires_grad=True),
            torch.rand(2, 3, dtype=torch.float64, device="cuda:1", requires_grad=True),
            torch.rand(2, 3, dtype=torch.float32, device="cuda:1", requires_grad=True),
            torch.rand(2, 3, dtype=torch.float16, device="cuda:1", requires_grad=True),
            torch.rand(2, 3, dtype=torch.bfloat16, device="cuda:1", requires_grad=True),
            torch.randint(
                1024, (2, 3), dtype=torch.int64, device="cuda:1", requires_grad=False
            ),
        ]

        for p in params:
            if p.requires_grad:
                p.grad = torch.rand_like(p, device=p.device, dtype=p.dtype)

        kIterations = 7 if impl == "foreach" else 1
        optim_inputs = optim_info.optim_inputs_func(device=device)
        optim_cls = optim_info.optim_cls
        for optim_input in optim_inputs:
            updated_params, state = [], []
            kwargs = deepcopy(optim_input.kwargs)
            if kwargs.get("capturable", False) and _get_device_type(device) == "cpu":
                # capturable is not supported on CPU
                continue
            for use_impl in (False, True):
                kwargs[impl] = use_impl
                params_clone = []
                for p in params:
                    p_clone = p.detach().clone()
                    if p.requires_grad:
                        p_clone.requires_grad = True
                        p_clone.grad = p.grad.detach().clone()
                        params_clone.append(p_clone)

                optimizer = optim_cls(params_clone, **kwargs)
                for _ in range(kIterations):
                    optimizer.step()

                state.append(optimizer.state)
                updated_params.append(params_clone)

            og_state, new_state = state
            for og_p, new_p in zip(updated_params[0], updated_params[1]):
                # Increasing the tolerance as we are collating lots of ops together for optimizers and
                # the designated tolerances are for single op only.
                single_rtol, single_atol = torch.testing._comparison.get_tolerances(
                    new_p.dtype, rtol=None, atol=None
                )
                rtol = 5 * single_rtol
                atol = 5 * single_atol

                self.assertEqual(og_p, new_p, rtol=rtol, atol=atol)

                # check that optimizer states are the same
                og_p_state = og_state[og_p]
                new_p_state = new_state[new_p]

                for k in og_p_state:
                    actual = new_p_state[k]
                    self.assertEqual(og_p_state[k], actual, rtol=rtol, atol=atol)