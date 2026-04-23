def run_benchmarks(operators, shapes):
    if operators is None:
        operators = OPERATORS
    else:
        operators = [globals()[k] for k in operators.split(",")]
    if shapes is None:
        shapes = SHAPES
    else:
        shapes = [globals()[k] for k in shapes.split(",")]

    print("fuser,device,operator,shape,time")
    for shape, operator in itertools.product(shapes, operators):
        nargs = len(inspect.signature(operator).parameters)
        args = shape()
        if nargs > len(args):
            args = list(args)
            args += [args[-1]] * (nargs - len(args))
        args = args[:nargs]
        args = [arg.to("cuda") for arg in args]

        result = benchmark(operator, args)
        print(
            ",".join(
                [
                    "eager",
                    args[0].device.type,
                    operator.__name__,
                    shape.__name__,
                    micros(result),
                ]
            )
        )

        def bench(name):
            nnc_op = torch.jit.trace(operator, args)
            result = benchmark(nnc_op, args)
            print(
                ",".join(
                    [
                        name,
                        args[0].device.type,
                        operator.__name__,
                        shape.__name__,
                        micros(result),
                    ]
                )
            )
            sys.stdout.flush()

        with_nnc()
        bench("nnc")
        with_nvfuser()
        bench("nvfuser")
        with_legacy()
        bench("legacy")