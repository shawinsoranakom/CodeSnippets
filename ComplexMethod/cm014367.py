def bench_all(
        model : torch.nn.Module | Callable,
        sample_input: torch.Tensor | Any,
        num_iters : int = 5,
        optimizer: torch.optim.Optimizer | None = None,
        loss_fn : torch.nn.Module | Callable | None = None,
    ):
        """
        This is a simple utility that can be used to benchmark torch.compile
        In particular it ensures that your GPU is setup to use tensor cores if it supports its
        It also tries out all the main backends and prints a table of results so you can easily compare them all
        Many of the backendds have their own optional dependencies so please pip install them separately

        You will get one table for inference and another for training
        If you'd like to leverage this utility for training make sure to pass in a torch.optim.Optimizer

        The important warnings are
        Your GPU supports tensor cores
        we will enable it automatically by setting `torch.set_float32_matmul_precision('high')`

        If a compilation fails for any reason including the dependency not being included
        then we will print Failed to compile {backend} with mode {mode}
        """
        field_names = ["Train/Inference", "Backend", "Mode", "Compilation Time", "Average Running Time"]
        table = []


        eager_time = None
        torch._dynamo.reset()
        _, eager_time = benchmark_compile(model, sample_input, num_iters, None, None, optimizer)
        table.append(
            [("Training" if optimizer else "Inference"), "Eager", "-", "-", f"{eager_time} ms"]
        )

        for backend in torch._dynamo.list_backends():

            if backend == "inductor":
                mode_options = cast(list[str | None], list(torch._inductor.list_mode_options().keys())) + [None]
                for mode in mode_options:
                    if mode == "default":
                        continue
                    torch._dynamo.reset()
                    try:
                        if torch.cuda.is_available():
                            _enable_tensor_cores()
                        compilation_time, running_time = benchmark_compile(
                            model, sample_input, num_iters, backend, mode, optimizer, loss_fn)
                    finally:
                        if torch.cuda.is_available():
                            _disable_tensor_cores()
                            table.append([
                                ("Training" if optimizer else "Inference"),
                                # pyrefly: ignore [redundant-condition]
                                backend if backend else "-",
                                mode if mode is not None else "-",
                                f"{compilation_time} ms " if compilation_time else "-",
                                f"{running_time} ms " if running_time else "-",
                            ])

            else:
                torch._dynamo.reset()
                compilation_time, running_time = benchmark_compile(
                    model, sample_input, num_iters, backend, None, optimizer, loss_fn)

                if running_time is not None:
                    table.append([
                        ("Training" if optimizer else "Inference"),
                        backend, "-",
                        f"{compilation_time} ms " or "-",
                        f"{running_time} ms ",
                    ])


        # pyrefly: ignore [not-callable]
        return tabulate(table, headers=field_names, tablefmt="github")