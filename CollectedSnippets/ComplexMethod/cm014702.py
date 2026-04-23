def test_tensor_lr(self, device, dtype, optim_info, num_dim):
        optim_cls = optim_info.optim_cls

        lr_devices = [device]
        if _get_device_type(device) != "cpu":
            lr_devices.append("cpu")

        # Skip differentiable testing for now, see https://github.com/pytorch/pytorch/issues/116490
        all_optim_inputs = _get_optim_inputs_including_global_cliquey_kwargs(
            device, dtype, optim_info, skip=("differentiable",)
        )
        for optim_input, lr_device in product(all_optim_inputs, lr_devices):
            weight = Parameter(torch.randn((10, 5), device=device, dtype=dtype))
            weight_c = weight.detach().clone().requires_grad_(True)
            bias = Parameter(torch.randn((10), device=device, dtype=dtype))
            bias_c = bias.detach().clone().requires_grad_(True)
            inpt = torch.randn(5, device=device, dtype=dtype)

            kwargs = optim_input.kwargs
            if "lr" in kwargs:
                del kwargs["lr"]

            params = [weight, bias] if optim_cls.__name__ != "Muon" else [weight]
            kwargs["lr"] = 1.0 if optim_info.step_requires_closure else 1e-3
            optimizer_r = optim_cls(params, **kwargs)

            try:
                kwargs["lr"] = (
                    torch.tensor(kwargs["lr"]).reshape([1] * num_dim).to(lr_device)
                )
                params_c = [weight_c, bias_c]
                if optim_cls.__name__ == "Muon":
                    params_c = [weight_c]
                optimizer = optim_cls(params_c, **kwargs)
            except ValueError as e:
                self.assertRegex(str(e), ".*lr as a Tensor is not supported.*")
                continue

            def closure(optim, w, b, i):
                optim.zero_grad()
                wo = w.mv(i) if optim_cls.__name__ == "Muon" else w.mv(i) + b
                loss = wo.pow(2).sum()
                loss.backward()
                if optim_info.only_supports_sparse_grads:
                    # For this test, we naively convert the Tensor layout, which we know does
                    # NOT represent the expected use case for optims like SparseAdam!
                    w.grad = w.grad.to_sparse()
                    b.grad = b.grad.to_sparse()
                return loss

            for _ in range(5):
                if optim_info.step_requires_closure:
                    optimizer_r.step(
                        functools.partial(closure, optimizer_r, weight, bias, inpt)
                    )
                    optimizer.step(
                        functools.partial(closure, optimizer, weight_c, bias_c, inpt)
                    )
                else:
                    closure(optimizer_r, weight, bias, inpt)
                    optimizer_r.step()
                    closure(optimizer, weight_c, bias_c, inpt)
                    optimizer.step()

                self.assertEqual(weight, weight_c)
                if optim_cls.__name__ != "Muon":
                    self.assertEqual(bias, bias_c)