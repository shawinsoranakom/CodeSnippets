def _test_optimizer_bitwise(
        test_case,
        optim_cls,
        kernel_count=None,
        num_steps=10,
        **optim_kwargs,
    ):
        """Helper to test optimizer bitwise equality."""
        torch._dynamo.reset()
        torch._inductor.metrics.reset()
        torch.manual_seed(42)

        input = torch.ones([10, 10], device=GPU_TYPE)
        model_eager = torch.nn.Sequential(
            *[torch.nn.Linear(10, 10, device=GPU_TYPE) for _ in range(2)]
        )
        model_eager(input).sum().backward()

        model_compiled = deepcopy(model_eager)
        model_compiled(input).sum().backward()

        opt_eager = optim_cls(model_eager.parameters(), **optim_kwargs)
        opt_compiled = optim_cls(model_compiled.parameters(), **optim_kwargs)
        compiled_step = compile_opt(opt_compiled)

        with torch.set_grad_enabled(False):
            for step in range(num_steps):
                compiled_step()
                opt_eager.step()

                # Check bitwise equality
                for i, (p_eager, p_compiled) in enumerate(
                    zip(model_eager.parameters(), model_compiled.parameters())
                ):
                    test_case.assertEqual(
                        p_eager,
                        p_compiled,
                        atol=0,
                        rtol=0,
                        msg=f"Step {step + 1}, param {i}: params differ",
                    )

        # Also check optimizer state
        for p_eager, p_compiled in zip(
            model_eager.parameters(), model_compiled.parameters()
        ):
            for key in opt_eager.state[p_eager]:
                eager_val = opt_eager.state[p_eager][key]
                compiled_val = opt_compiled.state[p_compiled][key]
                if isinstance(eager_val, torch.Tensor):
                    test_case.assertEqual(
                        eager_val,
                        compiled_val,
                        atol=0,
                        rtol=0,
                        msg=f"State '{key}' differs",
                    )

        if kernel_count is not None and test_case.check_kernel_count:
            if isinstance(kernel_count, types.LambdaType):
                kernel_count(str(torch._inductor.metrics.generated_kernel_count))
            else:
                test_case.assertEqual(
                    torch._inductor.metrics.generated_kernel_count, kernel_count
                )