def compile_fx_aot(
    model_: GraphModule,
    example_inputs_: list[InputType],
    inner_compile: _CompileFxCallable = compile_fx_inner,
    config_patches: dict[str, Any] | None = None,
) -> list[str | Weights] | str | GraphModule:
    assert isinstance(model_, GraphModule), model_

    # [See NOTE] Unwrapping subclasses AOT
    unwrap_tensor_subclass_parameters(model_)

    # pyrefly: ignore [annotation-mismatch, redefinition]
    config_patches: dict[str, Any] = copy.deepcopy(config_patches or {})

    if not (config_patches.get("fx_wrapper", False) or config.fx_wrapper):
        # If fx_wrapper is not set, then set cpp_wrapper
        config_patches["cpp_wrapper"] = True

    output_path = config_patches.get(
        "aot_inductor.output_path", config.aot_inductor.output_path
    )

    if output_path:
        assert not output_path.endswith(".pt2"), (
            "The output path for aot_compile should not have an extension with .pt2 "
            "this is for specifying the output path for the .so in AOTInductor. "
            "If you would like to package the AOTInductor generated files "
            "into a pt2, please call `torch._inductor.aoti_compile_and_package`."
        )
    else:
        config_patches = {
            **config_patches,
            "aot_inductor.output_path": code_hash(model_.code),
        }

    from .utils import maybe_aoti_standalone_config

    config_patches = maybe_aoti_standalone_config(config_patches)

    extern_node_serializer = config_patches.pop("extern_node_serializer", None)
    saved_compile_id = model_.meta.get("dynamo_compile_id", None)
    saved_compile_context = torch._guards.CompileContext(saved_compile_id)
    with (
        V.set_aot_compilation(True),
        torch._guards.compile_context(saved_compile_context),
        chromium_event_timed(
            "compile_fx_aot",
            log_pt2_compile_event=True,
            reset_event_log_on_exit=True,
        ),
        get_metrics_context(),
    ):
        compiled_artifacts = compile_fx(
            model_,
            example_inputs_,
            inner_compile=functools.partial(
                inner_compile,
                extern_node_serializer=extern_node_serializer,
            ),
            config_patches=config_patches,
        )

        assert isinstance(compiled_artifacts, CompiledAOTI)

        return compiled_artifacts.filename