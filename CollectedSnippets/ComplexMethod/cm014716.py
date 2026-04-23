def test_state_dict_with_cuda_params(self, device, dtype, optim_info):
        optim_cls = optim_info.optim_cls

        # Skip differentiable testing for now, see https://github.com/pytorch/pytorch/issues/116490
        # We limit our configs to CPU only, because we will be moving them to CUDA later
        cpu_optim_inputs = _get_optim_inputs_including_global_cliquey_kwargs(
            "cpu", dtype, optim_info, skip=("differentiable",)
        )

        # Needed for second order optims like LBFGS
        closure_loss = torch.rand(1, device=device, dtype=dtype)

        def closure():
            return closure_loss if optim_info.step_requires_closure else None

        for optim_input in cpu_optim_inputs:
            if (
                "fused" in optim_input.kwargs
                and "cuda" not in optim_info.supports_fused_on
            ):
                self.skipTest(
                    f"cuda is not supported for fused on {optim_cls.__name__}"
                )
            params = [
                Parameter(torch.randn(2, 3, device="cpu", dtype=dtype))
                for _ in range(2)
            ]
            for p in params:
                p.grad = torch.randn_like(p)
                if optim_info.only_supports_sparse_grads:
                    # For this test, we naively convert the Tensor layout, which we know does
                    # NOT represent the expected use case for optims like SparseAdam!
                    p.grad = p.grad.to_sparse()

            optimizer = optim_cls(params, **optim_input.kwargs)

            for _ in range(3):
                optimizer.step(closure)

            with torch.no_grad():
                params_cuda = [p.to(device="cuda") for p in params]
                for i, p in enumerate(params_cuda):
                    p.grad = params[i].grad.to(device="cuda")
            optimizer_cuda = optim_cls(params_cuda, **optim_input.kwargs)

            state_dict_cpu = deepcopy(optimizer.state_dict())
            state_dict_cuda = deepcopy(optimizer.state_dict())
            optimizer_cuda.load_state_dict(state_dict_cuda)

            # Make sure state_dict_cuda isn't modified by merely calling load_state_dict
            self.assertEqual(state_dict_cpu, state_dict_cuda)

            # Make sure that device of state['step'] is still CPU _unless_ torch.compile() added a capturable!
            capturable = state_dict_cpu["param_groups"][0].get("capturable", False)
            fused = state_dict_cpu["param_groups"][0].get("fused", False)
            new_state_dict = optimizer_cuda.state_dict()
            for state_cpu, state_cuda in zip(
                state_dict_cpu["state"].values(), new_state_dict["state"].values()
            ):
                if "step" in state_cpu and torch.is_tensor(state_cpu["step"]):
                    self.assertEqual(
                        state_cuda["step"].device.type,
                        "cuda" if capturable or fused else "cpu",
                    )

            for _ in range(5):
                optimizer.step(closure)
                optimizer_cuda.step(closure)
                self.assertEqual(params, params_cuda)
                self.assertEqual(optimizer.state_dict(), optimizer_cuda.state_dict())