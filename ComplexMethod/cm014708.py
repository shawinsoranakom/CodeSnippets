def test_fused_does_not_step_if_foundinf(self, device, dtype, optim_info):
        if device not in optim_info.supports_fused_on:
            self.skipTest(
                f"{device} is not supported for fused on {optim_info.optim_cls.__name__}"
            )
        optim_cls = optim_info.optim_cls
        optim_inputs = optim_info.optim_inputs_func(device=device)
        num_params = 5
        for optim_input in optim_inputs:
            for no_grad_scale in (False, True):
                params = [
                    torch.ones((1,), device=device, dtype=dtype)
                    for _ in range(num_params)
                ]
                params_c = [param.detach().clone() for param in params]
                for p in params:
                    p.grad = torch.ones_like(p)
                optimizer = optim_cls(params, fused=True, **optim_input.kwargs)
                optimizer.grad_scale = (
                    None
                    if no_grad_scale
                    else torch.ones((1,), dtype=dtype, device=device)
                )
                optimizer.found_inf = torch.ones((), dtype=dtype, device=device)
                optimizer.step()
                for p in params:
                    if "step" in optimizer.state[p]:
                        self.assertEqual(
                            torch.zeros((), dtype=dtype, device=device),
                            optimizer.state[p]["step"],
                        )
                self.assertEqual(params, params_c)