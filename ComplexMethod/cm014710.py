def test_param_groups_lr(self, device, dtype, optim_info):
        optim_cls = optim_info.optim_cls
        # Skip differentiable testing for now, see https://github.com/pytorch/pytorch/issues/116490
        all_optim_inputs = _get_optim_inputs_including_global_cliquey_kwargs(
            device, dtype, optim_info, skip=("differentiable",)
        )
        for optim_input in all_optim_inputs:
            # optim_input.kwargs will be the param group kwargs, which should have >0 lr
            if "lr" not in optim_input.kwargs or optim_input.kwargs["lr"] == 0:
                optim_input.kwargs["lr"] = 1e-3
            outer_kwargs = {"lr": 1e-28}
            if optim_cls.__name__ == "Rprop":
                # Allow min step size to be 0
                outer_kwargs["step_sizes"] = (0, 50)

            weight = Parameter(torch.randn((10, 5), device=device, dtype=dtype))
            bias = Parameter(torch.randn((10), device=device, dtype=dtype))
            irrelevant = Parameter(torch.randn((2, 2), device=device, dtype=dtype))
            irrelevant_clone = irrelevant.clone()
            input = torch.randn(5, device=device, dtype=dtype)
            params = [weight, bias] if optim_cls.__name__ != "Muon" else [weight]
            optimizer = optim_cls(
                [
                    dict(params=params, **optim_input.kwargs),
                    dict(params=[irrelevant]),
                ],
                **outer_kwargs,
            )

            wo = (
                weight.mv(input)
                if optim_cls.__name__ == "Muon"
                else weight.mv(input) + bias
            )
            loss = wo.pow(2).sum()
            initial_value = loss.item()
            for _ in range(20):
                optimizer.zero_grad()
                wo = (
                    weight.mv(input)
                    if optim_cls.__name__ == "Muon"
                    else weight.mv(input) + bias
                )
                loss = wo.pow(2).sum()
                loss.backward()
                irrelevant.grad = torch.rand_like(irrelevant)
                if optim_info.only_supports_sparse_grads:
                    # For this test, we naively convert the Tensor layout, which we know does
                    # NOT represent the expected use case for optims like SparseAdam!
                    weight.grad = weight.grad.to_sparse()
                    bias.grad = bias.grad.to_sparse()
                    irrelevant.grad = irrelevant.grad.to_sparse()
                optimizer.step()

            # Test that the direction of loss moved appropriately
            if optim_input.kwargs.get("maximize", False):
                self.assertGreater(loss.item(), initial_value)
            else:
                self.assertLess(loss.item(), initial_value)

            # Test that irrelevant parameters were not updated since lr was almost 0
            self.assertEqual(irrelevant, irrelevant_clone)