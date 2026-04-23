def test_correctness(self, device, dtype, optim_info, use_closure):
        torch.get_device_module(device).manual_seed_all(0)
        torch.manual_seed(0)
        random.seed(0)
        optim_cls = optim_info.optim_cls
        all_optim_inputs = _get_optim_inputs_including_global_cliquey_kwargs(
            device, dtype, optim_info, skip=("differentiable",)
        )

        if optim_info.step_requires_closure and not use_closure:
            return

        for optim_input in all_optim_inputs:
            kwargs = optim_input.kwargs

            use_scheduler = isinstance(kwargs.get("lr", None), torch.Tensor)
            scheduler_classes = (
                list(LR_SCHEDULER_TO_KWARGS.keys()) if use_scheduler else [None]
            )

            for scheduler_cls in scheduler_classes:
                torch._dynamo.reset()
                torch._inductor.metrics.reset()
                input = torch.ones([10, 10], device=device)
                model_eager = torch.nn.Sequential(
                    *[
                        torch.nn.Linear(10, 10, device=device, bias=False)
                        for _ in range(2)
                    ]
                )
                model_eager(input).sum().backward()
                model_compiled = deepcopy(model_eager)
                model_compiled(input).sum().backward()

                if optim_cls is SparseAdam:
                    for param in model_eager.parameters():
                        param.grad = param.grad.to_sparse()
                    for param in model_compiled.parameters():
                        param.grad = param.grad.to_sparse()

                opt_compiled = optim_cls(
                    model_compiled.parameters(), **deepcopy(kwargs)
                )
                opt_eager = optim_cls(model_eager.parameters(), **deepcopy(kwargs))
                if scheduler_cls:
                    scheduler_compiled = create_scheduler(scheduler_cls, opt_compiled)
                    scheduler_eager = create_scheduler(scheduler_cls, opt_eager)
                    # some schedulers only change after at least an epoch has passed
                    scheduler_compiled.last_epoch = 1
                    scheduler_eager.last_epoch = 1

                num_steps = 2
                if use_closure:

                    @torch.compile()
                    def fn():
                        def closure():
                            loss = model_compiled(input).sum()
                            loss.backward()
                            if optim_info.only_supports_sparse_grads:
                                for param in model_compiled.parameters():
                                    param.grad = param.grad.to_sparse()
                            return loss

                        opt_compiled.step(closure)
                        if scheduler_cls:
                            call_scheduler(scheduler_compiled)

                    def closure_eager():
                        loss = model_eager(input).sum()
                        loss.backward()
                        if optim_info.only_supports_sparse_grads:
                            for param in model_eager.parameters():
                                param.grad = param.grad.to_sparse()

                        return loss

                    for _ in range(num_steps):
                        opt_eager.step(closure_eager)
                        if scheduler_cls:
                            call_scheduler(scheduler_eager)
                else:

                    @torch.compile()
                    def fn():
                        opt_compiled.step()
                        if scheduler_cls:
                            call_scheduler(scheduler_compiled)

                    for _ in range(num_steps):
                        opt_eager.step()
                        if scheduler_cls:
                            call_scheduler(scheduler_eager)

                for _ in range(num_steps):
                    fn()

                check_optim(
                    self,
                    optim_cls,
                    model_eager.parameters(),
                    model_compiled.parameters(),
                    opt_eager.state,
                    opt_compiled.state,
                )