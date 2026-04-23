def test_forloop_goes_right_direction_multigpu(
        self, device, dtype, optim_info, with_lrsched
    ):
        optim_cls = optim_info.optim_cls
        schedulers_constructors = (
            optim_info.scheduler_inputs if with_lrsched else [None]
        )
        for schedulers_constructor in schedulers_constructors:
            # We need a fresh set of inputs if we have a tensor LR
            # to not carry mutations across iterations.
            optim_inputs = optim_info.optim_inputs_func(device=device)
            for optim_input in optim_inputs:
                if "foreach" in optim_info.supported_impls:
                    optim_input.kwargs["foreach"] = False  # force forloop

                weight = Parameter(torch.randn((10, 5), device="cuda:0", dtype=dtype))
                bias = Parameter(torch.randn((10), device="cuda:1", dtype=dtype))
                inpt = torch.randn(5, device="cuda:0", dtype=dtype)

                params = [weight, bias] if optim_cls.__name__ != "Muon" else [weight]
                optimizer = optim_cls(params, **optim_input.kwargs)
                schedulers = [
                    s(optimizer)
                    for s in (schedulers_constructor if schedulers_constructor else [])
                ]

                def closure():
                    optimizer.zero_grad()
                    wo = (
                        weight.mv(inpt).cuda(1)
                        if optim_cls.__name__ == "Muon"
                        else weight.mv(inpt).cuda(1) + bias
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
                    loss = optimizer.step(closure)
                    for scheduler in schedulers:
                        if isinstance(scheduler, ReduceLROnPlateau):
                            scheduler.step(loss)
                        else:
                            scheduler.step()

                if optim_input.kwargs.get("maximize", False):
                    self.assertGreater(closure().item(), initial_value)
                else:
                    self.assertLess(closure().item(), initial_value)