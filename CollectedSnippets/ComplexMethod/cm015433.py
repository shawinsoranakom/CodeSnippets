def _test_compile(
        self,
        *,
        no_sync: bool,
        setup_func: Callable | None = None,
        no_inductor: bool = False,
        no_compile_forward: bool = False,
        checkpoint: bool = False,
        device: str | torch.device,
    ):
        self.create_pg(device)
        torch._dynamo.config.optimize_ddp = "python_reducer"
        torch.manual_seed(123)
        if device_type == "xpu":
            torch.use_deterministic_algorithms(True, warn_only=True)
        model = Net(checkpoint=checkpoint).to(device)
        input = torch.randn([1, DIM], device=device)

        compiled_replicate_model = replicate(deepcopy(model))
        if not no_compile_forward:
            compiled_replicate_model = torch.compile(
                compiled_replicate_model, fullgraph=False
            )
        compiled_replicate_optim = torch.optim.Adam(
            compiled_replicate_model.parameters()
        )
        compiled_ddp_model = DDP(deepcopy(model))
        if not no_compile_forward:
            compiled_ddp_model = torch.compile(compiled_ddp_model, fullgraph=True)
        compiled_ddp_optim = torch.optim.Adam(compiled_ddp_model.parameters())
        model = replicate(model)
        optim = torch.optim.Adam(model.parameters())

        if setup_func:
            setup_func(model, compiled_replicate_model, compiled_ddp_model)

        models = [model, compiled_replicate_model, compiled_ddp_model]
        optims = [optim, compiled_replicate_optim, compiled_ddp_optim]
        sync_contexts = [
            contextlib.nullcontext(),
            contextlib.nullcontext(),
            compiled_ddp_model.no_sync(),
        ]

        # Run multiple iterations so that we could test no_sync
        for i in range(2):
            # Setting a different random seed so that if the allreduces are not
            # executed correctly, the gradients won't be correct compared to the
            # eager DDP.
            torch.manual_seed(123 + self.rank + i)
            input = torch.randn([1, DIM], device=device)

            for model_idx in range(3):
                if no_sync and i % 2 == 0:
                    context = sync_contexts[model_idx]
                    if model_idx <= 1:
                        models[model_idx].set_requires_gradient_sync(False)
                else:
                    context = contextlib.nullcontext()
                    if model_idx <= 1:
                        models[model_idx].set_requires_gradient_sync(True)
                context = contextlib.nullcontext()

                with context:
                    bwd_context = (
                        contextlib.nullcontext()
                        if model_idx == 0
                        else compiled_autograd._enable(compiler_fn(no_inductor))
                    )
                    with bwd_context:
                        loss = models[model_idx](input).sum()
                        loss.backward()

            if not no_sync or i % 2 == 1:
                for p1, p2, p3 in zip(
                    model.parameters(),
                    compiled_replicate_model.parameters(),
                    compiled_ddp_model.parameters(),
                ):
                    self.assertEqual(p1.grad, p2.grad)
                    self.assertEqual(p1.grad, p3.grad)
                for optim in optims:
                    optim.step()
                    optim.zero_grad()

        self.assertEqual(
            tuple(model.parameters()), tuple(compiled_replicate_model.parameters())
        )
        self.assertEqual(
            tuple(model.parameters()), tuple(compiled_ddp_model.parameters())
        )
        dist.destroy_process_group()