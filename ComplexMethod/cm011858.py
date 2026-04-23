def aot_inductor_minifier_wrapper(
    func: Callable[..., str],
    exported_program: torch.export.ExportedProgram,
    *,
    inductor_configs: dict[str, Any],
    package_path: FileLike | None = None,
) -> str:
    from torch._dynamo.debug_utils import AccuracyError
    from torch._dynamo.repro.aoti import dump_to_minify
    from torch._inductor import config
    from torch._inductor.compile_fx import _aoti_flatten_inputs

    use_minifier = config.aot_inductor.dump_aoti_minifier

    gm = exported_program.module(check_guards=False)
    assert isinstance(gm, torch.fx.GraphModule)

    args, kwargs = exported_program.example_inputs

    try:
        if use_minifier and config.aot_inductor.repro_level == 3:
            # Always dump the original module in case we have segfaults
            dump_to_minify(
                exported_program,
                "aot_inductor",
                options=inductor_configs,
            )
        if use_minifier and config.aot_inductor.repro_level == 4:
            # Check for accuracy
            # We will first flatten the inputs before compiling and checking for accuracy.
            # This is ok because we will flatten the inputs in the minifier anyway.
            gm_copy = copy.deepcopy(gm)
            example_inputs_copy = copy.deepcopy(exported_program.example_inputs)
            config_copy = copy.deepcopy(inductor_configs)
            flat_example_inputs, config_copy = _aoti_flatten_inputs(
                gm_copy,
                example_inputs_copy[0],
                example_inputs_copy[1],
                options=config_copy,
            )
            tuple_inputs = tuple(flat_example_inputs)
            flattened_ep = torch.export.export(gm_copy, tuple_inputs, strict=False)
            func(
                flattened_ep.module(check_guards=False),
                tuple_inputs,
                inductor_configs=config_copy,
                package_path=package_path,
                load_and_run=True,
                check_accuracy="accuracy",
            )

        return func(
            gm,
            args,
            kwargs,
            inductor_configs=inductor_configs,
            package_path=package_path,
            load_and_run=use_minifier,
        )
    except AccuracyError as e:
        dump_to_minify(
            exported_program,
            "aot_inductor_accuracy",
            command="minify",
            options=inductor_configs,
        )
        log.warning("Accuracy failed")
        raise e
    except Exception as e:
        if use_minifier:
            command = "minify"

            if config.aot_inductor.repro_level == 1:
                command = "run"

            dump_to_minify(
                exported_program,
                "aot_inductor",
                command=command,
                options=inductor_configs,
            )
        raise e