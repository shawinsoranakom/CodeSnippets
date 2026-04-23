def test_forloop_goes_right_direction(
        self, device, dtype, optim_info, contiguous, with_lrsched
    ):
        optim_cls = optim_info.optim_cls
        schedulers_constructors = (
            optim_info.scheduler_inputs if with_lrsched else [None]
        )

        for schedulers_constructor in schedulers_constructors:
            # with tensor LR we need fresh inputs for each scheduler
            # or mutating it will carry across iters
            optim_inputs = optim_info.optim_inputs_func(device=device)
            for optim_input in optim_inputs:
                if "foreach" in optim_info.supported_impls:
                    optim_input.kwargs["foreach"] = False  # force forloop
                if contiguous:
                    weight = Parameter(torch.randn((10, 5), device=device, dtype=dtype))
                    bias = Parameter(torch.randn((10), device=device, dtype=dtype))
                else:
                    weight = Parameter(
                        torch.randn((10, 5, 2), device=device, dtype=dtype)[..., 0]
                    )
                    bias = Parameter(
                        torch.randn((10, 2), device=device, dtype=dtype)[..., 0]
                    )
                input = torch.randn(5, device=device, dtype=dtype)

                params = [weight, bias] if optim_cls.__name__ != "Muon" else [weight]
                optimizer = optim_cls(params, **optim_input.kwargs)
                schedulers = [
                    s(optimizer)
                    for s in (schedulers_constructor if schedulers_constructor else [])
                ]

                def closure():
                    optimizer.zero_grad()
                    wo = (
                        weight.mv(input)
                        if optim_cls.__name__ == "Muon"
                        else weight.mv(input) + bias
                    )
                    loss = wo.pow(2).sum()
                    loss.backward()
                    if optim_info.only_supports_sparse_grads:
                        # For this test, we naively convert the Tensor layout, which we know does
                        # NOT represent the expected use case for optims like SparseAdam!
                        weight.grad = weight.grad.to_sparse()
                        bias.grad = bias.grad.to_sparse()
                    return loss

                initial_value = closure().item()
                for _ in range(20):
                    if optim_info.step_requires_closure:
                        loss = optimizer.step(closure)
                    else:
                        loss = closure()
                        optimizer.step()

                    for scheduler in schedulers:
                        if isinstance(scheduler, ReduceLROnPlateau):
                            scheduler.step(loss)
                        else:
                            scheduler.step()

                if optim_input.kwargs.get("maximize", False):
                    self.assertGreater(closure().item(), initial_value)
                else:
                    self.assertLess(closure().item(), initial_value)