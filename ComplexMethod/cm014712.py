def test_state_dict_deterministic(
        self, device, dtype, optim_info, is_named_optim0, is_named_optim1
    ):
        optim_cls = optim_info.optim_cls

        # Skip differentiable testing for now, see https://github.com/pytorch/pytorch/issues/116490
        all_optim_inputs = _get_optim_inputs_including_global_cliquey_kwargs(
            device, dtype, optim_info, skip=("differentiable",)
        )
        weight = Parameter(
            torch.randn(2, 3, requires_grad=True, device=device, dtype=dtype)
        )
        bias = Parameter(torch.randn(2, requires_grad=True, device=device, dtype=dtype))
        input = torch.randn(3, requires_grad=True, device=device, dtype=dtype)
        params = [weight, bias]
        if optim_cls.__name__ == "Muon":
            params = [weight]

        def make_named_param(param, is_named):
            if not is_named:
                return param
            return [(f"name{i}", p) for i, p in enumerate(param)]

        def without_param_names(state_dict):
            new_state_dict = deepcopy(state_dict)
            for pg in new_state_dict["param_groups"]:
                pg.pop("param_names", None)
            return new_state_dict

        def fwd_bwd(optim, w, b, i):
            optim.zero_grad()
            wo = w.mv(i) if optim_cls.__name__ == "Muon" else w.mv(i) + b
            loss = wo.pow(2).sum()
            loss.backward()
            if optim_info.only_supports_sparse_grads:
                if w.grad is not None:
                    w.grad = w.grad.to_sparse()
                if b.grad is not None:
                    b.grad = b.grad.to_sparse()
            return loss

        for optim_input in all_optim_inputs:
            params_in = make_named_param(params, is_named=is_named_optim0)
            optimizer = optim_cls(params_in, **optim_input.kwargs)
            closure = functools.partial(fwd_bwd, optimizer, weight, bias, input)

            # Prime the optimizer
            for _ in range(10):
                if optim_info.step_requires_closure:
                    optimizer.step(closure)
                else:
                    closure()
                    optimizer.step()

            # Clone the weights and construct a new optimizer for them
            with torch.no_grad():
                weight_c = Parameter(weight.clone())
                bias_c = Parameter(bias.clone())
            params_c_list = (
                [weight_c, bias_c] if optim_cls.__name__ != "Muon" else [weight_c]
            )
            params_c = make_named_param(params_c_list, is_named=is_named_optim1)
            optimizer_c = optim_cls(params_c, **optim_input.kwargs)
            closure_c = functools.partial(fwd_bwd, optimizer_c, weight_c, bias_c, input)

            # Load the state dict from the original optimizer into the new one
            optimizer_c.load_state_dict(deepcopy(optimizer.state_dict()))

            # Run both optimizers in parallel
            for _ in range(10):
                if optim_info.step_requires_closure:
                    optimizer.step(closure)
                    optimizer_c.step(closure_c)
                else:
                    closure()
                    closure_c()
                    optimizer.step()
                    optimizer_c.step()

                self.assertEqual(weight, weight_c)
                if optim_cls.__name__ != "Muon":
                    self.assertEqual(bias, bias_c)

            # Make sure state dict is deterministic with equal (not identical) parameters
            # Param names are optional and not needed to be the consistent.
            self.assertEqual(
                without_param_names(optimizer.state_dict()),
                without_param_names(optimizer_c.state_dict()),
            )

            # Make sure repeated parameters have identical representation (see #36831)
            optimizer_c.param_groups.extend(optimizer_c.param_groups)
            self.assertEqual(
                without_param_names(optimizer.state_dict())["param_groups"][-1],
                without_param_names(optimizer_c.state_dict())["param_groups"][-1],
            )