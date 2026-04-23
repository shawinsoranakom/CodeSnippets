def test_fn(self):
        stack = ExitStack()
        try:
            # https://github.com/pytorch/pytorch/issues/118715 for capturable Adagrad support
            # https://github.com/pytorch/pytorch/issues/118018 for capturable SGD support
            run_cudagraphs = device == "cuda" and optim_cls not in (Adagrad, SGD)
            if run_cudagraphs:
                stack.enter_context(config.patch({"triton.cudagraphs": True}))

            kwargs_compiled = deepcopy(kwargs)
            if isinstance(kwargs.get("lr"), torch.Tensor):
                kwargs["lr"] = kwargs["lr"].to(device)
                kwargs_compiled["lr"] = kwargs_compiled["lr"].to(device)

            if "betas" in kwargs and isinstance(kwargs["betas"][0], torch.Tensor):
                kwargs["betas"] = (
                    kwargs["betas"][0].to(device),
                    kwargs["betas"][1].to(device),
                )
                kwargs_compiled["betas"] = (
                    kwargs_compiled["betas"][0].to(device),
                    kwargs_compiled["betas"][1].to(device),
                )

            torch._dynamo.reset()
            torch._inductor.metrics.reset()
            input = torch.ones([10, 10], device=device)
            model_eager = torch.nn.Sequential(
                *[torch.nn.Linear(10, 10, device=device) for _ in range(2)]
            )
            model_eager(input).sum().backward()

            input = torch.ones([10, 10], device=device)
            model_compiled = deepcopy(model_eager)
            model_compiled(input).sum().backward()

            opt_eager = optim_cls(model_eager.parameters(), **kwargs)
            opt_compiled = optim_cls(model_compiled.parameters(), **kwargs_compiled)
            compiled_step = compile_opt(opt_compiled, closure=closure)

            if scheduler_cls:
                scheduler_compiled = create_scheduler(scheduler_cls, opt_compiled)
                scheduler_eager = create_scheduler(scheduler_cls, opt_eager)
                # some schedulers only change after at least an epoch has passed
                scheduler_compiled.last_epoch = 1
                scheduler_eager.last_epoch = 1

            with torch.set_grad_enabled(False):
                for _ in range(2):
                    compiled_step()
                    opt_eager.step()
                    if scheduler_cls:
                        call_scheduler(scheduler_eager)
                        call_scheduler(scheduler_compiled)

            check_optim(
                self,
                optim_cls,
                model_eager.parameters(),
                model_compiled.parameters(),
                opt_eager.state,
                opt_compiled.state,
            )

            if run_cudagraphs:
                self.check_cudagraphs_ran()

            if self.check_kernel_count:
                # currently, we compile the step and the rest of the computation
                # separately because the step is a single element tensor
                # hence, the usual kernel count is 2
                if isinstance(kernel_count, types.LambdaType):
                    kernel_count(str(torch._inductor.metrics.generated_kernel_count))
                else:
                    self.assertEqual(
                        torch._inductor.metrics.generated_kernel_count, kernel_count
                    )
        finally:
            stack.close()