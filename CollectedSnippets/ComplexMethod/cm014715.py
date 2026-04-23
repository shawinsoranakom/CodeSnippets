def test_load_nontensor_step(self, device, dtype, optim_info):
        optim_cls = optim_info.optim_cls

        # Skip differentiable testing for now, see https://github.com/pytorch/pytorch/issues/116490
        all_optim_inputs = _get_optim_inputs_including_global_cliquey_kwargs(
            device, dtype, optim_info, skip=("differentiable",)
        )
        params = [
            Parameter(torch.randn(2, 3, device=device, dtype=dtype)) for _ in range(2)
        ]
        for p in params:
            p.grad = torch.rand_like(p)
            if optim_info.only_supports_sparse_grads:
                # For this test, we naively convert the Tensor layout, which we know does
                # NOT represent the expected use case for optims like SparseAdam!
                p.grad = p.grad.to_sparse()

        # Needed for second order optims like LBFGS
        closure_loss = torch.rand(1, device=device, dtype=dtype)

        def closure():
            return closure_loss if optim_info.step_requires_closure else None

        for optim_input in all_optim_inputs:
            optimizer = optim_cls(params, **optim_input.kwargs)
            for _ in range(3):
                optimizer.step(closure)
            state_dict = deepcopy(optimizer.state_dict())
            for p_state in state_dict["state"].values():
                if "step" in p_state and torch.is_tensor(p_state["step"]):
                    p_state["step"] = p_state["step"].item()
            optimizer.load_state_dict(state_dict)
            optimizer.step(closure)