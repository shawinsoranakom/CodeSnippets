def materialize(benchmarks: FlatIntermediateDefinition) -> FlatDefinition:
    """Convert a heterogeneous benchmark into an executable state.

    This entails generation of TorchScript model artifacts, splitting
    GroupedBenchmarks into multiple TimerArgs, and tagging the results with
    AutoLabels.
    """
    results: list[tuple[Label, AutoLabels, TimerArgs]] = []

    for label, args in benchmarks.items():
        if isinstance(args, TimerArgs):
            # User provided an explicit TimerArgs, so no processing is necessary.
            auto_labels = AutoLabels(
                RuntimeMode.EXPLICIT, AutogradMode.EXPLICIT, args.language
            )
            results.append((label, auto_labels, args))

        else:
            if not isinstance(args, GroupedBenchmark):
                raise AssertionError(f"Expected GroupedBenchmark, but got {type(args)}")

            model_path: str | None = None
            if args.py_model_setup and args.torchscript:
                model_setup = (
                    f"{args.py_model_setup}\njit_model = torch.jit.script(model)"
                )

                # This is just for debugging. We just need a unique name for the
                # model, but embedding the label makes debugging easier.
                name: str = re.sub(r"[^a-z0-9_]", "_", "_".join(label).lower())
                name = f"{name}_{uuid.uuid4()}"

                model_path = _generate_torchscript_file(model_setup, name=name)

            for (runtime, autograd, language), num_threads in it.product(
                _ALL_MODES, args.num_threads
            ):
                if runtime == RuntimeMode.EXPLICIT or autograd == AutogradMode.EXPLICIT:
                    continue

                if runtime == RuntimeMode.JIT and not args.torchscript:
                    continue

                if autograd == AutogradMode.FORWARD_BACKWARD and not args.autograd:
                    continue

                stmt = _get_stmt(args, runtime, autograd, language)
                if stmt is None:
                    continue

                setup = _get_setup(args, runtime, language, stmt, model_path)

                global_setup: str = ""
                if language == Language.CPP and runtime == RuntimeMode.JIT:
                    global_setup = textwrap.dedent(
                        """
                        #include <string>
                        #include <vector>
                        #include <torch/script.h>
                    """
                    )

                autolabels = AutoLabels(runtime, autograd, language)
                timer_args = TimerArgs(
                    stmt=stmt,
                    setup=setup,
                    global_setup=global_setup,
                    num_threads=num_threads,
                    language=language,
                )

                results.append((label, autolabels, timer_args))

    return tuple(results)