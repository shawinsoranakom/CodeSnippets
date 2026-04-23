def test_can_load_older_state_dict(self, device, dtype, optim_info):
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
            optimizer = optim_cls(model.parameters(), **optim_input.kwargs)

            def fwd_bwd(optim, mod, i):
                optim.zero_grad()
                loss = mod(i).sum()
                loss.backward()
                return loss

            for _ in range(3):
                if optim_info.step_requires_closure:
                    optimizer.step(functools.partial(fwd_bwd, optimizer, model, input))
                else:
                    fwd_bwd(optimizer, model, input)
                    optimizer.step()

            # old_state_dict has all new flags del'd
            old_state_dict = deepcopy(optimizer.state_dict())
            old_state_dict_pg = old_state_dict["param_groups"]
            for group in old_state_dict_pg:
                for flag in optim_info.not_og_supported_flags:
                    if flag in group:
                        del group[flag]

            optimizer.load_state_dict(old_state_dict)

            # Make sure we can still step
            if optim_info.step_requires_closure:
                optimizer.step(functools.partial(fwd_bwd, optimizer, model, input))
            else:
                fwd_bwd(optimizer, model, input)
                optimizer.step()