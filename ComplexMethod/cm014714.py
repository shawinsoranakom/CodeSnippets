def test_can_load_from_to_named_state_dict(
        self, device, dtype, optim_info, is_named_optim0, is_named_optim1
    ):
        optim_cls = optim_info.optim_cls

        # Skip differentiable testing for now, see https://github.com/pytorch/pytorch/issues/116490
        all_optim_inputs = _get_optim_inputs_including_global_cliquey_kwargs(
            device, dtype, optim_info, skip=("differentiable",)
        )

        def _get_model_and_input_tensor(device, dtype, optim_cls):
            if optim_cls.__name__ == "Muon":
                # Muon only accepts 2D parameter.
                model = torch.nn.Linear(10, 4, bias=False)
                input = torch.rand(10, device=device, dtype=dtype)
            else:
                model = torch.nn.Sequential(
                    torch.nn.Conv2d(4, 2, 1, stride=2),
                    torch.nn.BatchNorm2d(2, eps=1e-05, momentum=0.1),
                )
                input = torch.rand(1, 4, 16, 16, device=device, dtype=dtype)
            model.to(dtype=dtype, device=device)
            return model, input

        for optim_input in all_optim_inputs:
            torch.manual_seed(1)
            model, input = _get_model_and_input_tensor(device, dtype, optim_cls)

            def fwd_bwd(optim, mod, i):
                optim.zero_grad()
                loss = mod(i).sum()
                loss.backward()
                return loss

            # test for parameters, named_parameters, and 2 groups:
            params_to_optimizer = (
                model.named_parameters() if is_named_optim0 else model.parameters()
            )
            optimizer = optim_cls(params_to_optimizer, **optim_input.kwargs)

            for _ in range(3):
                if optim_info.step_requires_closure:
                    optimizer.step(functools.partial(fwd_bwd, optimizer, model, input))
                else:
                    fwd_bwd(optimizer, model, input)
                    optimizer.step()

            # old_state_dict has all new flags del'd
            old_state_dict = deepcopy(optimizer.state_dict())

            params_to_optimizer2 = (
                model.named_parameters() if is_named_optim1 else model.parameters()
            )
            optimizer2 = optim_cls(params_to_optimizer2, **optim_input.kwargs)
            optimizer2.load_state_dict(old_state_dict)

            # Make sure we can still step
            if optim_info.step_requires_closure:
                optimizer2.step(functools.partial(fwd_bwd, optimizer2, model, input))
            else:
                fwd_bwd(optimizer2, model, input)
                optimizer2.step()

            ref_names = [p[0] for p in model.named_parameters()]
            # Make sure that param_names are preserved when provided to at least one of the optimizers
            if is_named_optim0 or is_named_optim1:
                self.assertEqual(
                    optimizer2.state_dict()["param_groups"][0]["param_names"],
                    ref_names,
                )