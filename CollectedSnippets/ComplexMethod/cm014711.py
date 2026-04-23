def test_step_is_noop_for_zero_grads(self, device, dtype, optim_info):
        optim_cls = optim_info.optim_cls
        all_optim_inputs = _get_optim_inputs_including_global_cliquey_kwargs(
            device, dtype, optim_info
        )
        param = torch.randn((5, 1), device=device, dtype=dtype, requires_grad=True)
        old_param = param.detach().clone()

        def closure():
            return torch.tensor([1], device=device, dtype=dtype)

        for optim_input in all_optim_inputs:
            kwargs = optim_input.kwargs

            # params will decay even if grads are empty if weight_decay != 0,
            # and capturable doesn't work for CPU tensors
            if kwargs.get("weight_decay", 0) != 0:
                continue

            # AdamW/Muon params will be updated regardless of grads due to lr, so make lr smaller
            if optim_cls.__name__ == "AdamW" or optim_cls.__name__ == "Muon":
                kwargs["lr"] = (
                    torch.tensor(1e-5)
                    if isinstance(kwargs.get("lr", 1e-5), torch.Tensor)
                    else 1e-5
                )

            if kwargs.get("differentiable", False):
                params = [param.detach()]
            else:
                params = [param]

            optimizer = optim_cls(params, **kwargs)
            if optim_info.only_supports_sparse_grads:
                # Intentionally construct a multidimensional empty v for the sparse grad
                # Single dim v passes the test while multidim correctly repros the issue
                # https://github.com/pytorch/pytorch/issues/82486
                i = torch.empty((1, 0), device=device, dtype=dtype)
                v = torch.empty((0, 1), device=device, dtype=dtype)
                params[0].grad = torch.sparse_coo_tensor(
                    i, v, (5, 1), device=device, dtype=dtype
                )
            else:
                params[0].grad = torch.zeros_like(params[0])
            optimizer.step(closure)
            self.assertEqual(old_param, params[0])