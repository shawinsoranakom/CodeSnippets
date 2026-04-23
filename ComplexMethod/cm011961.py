def compile_fx(
    model_: GraphModule,
    example_inputs_: Sequence[InputType],
    inner_compile: Callable[..., OutputCode] = compile_fx_inner,
    config_patches: dict[str, Any] | None = None,
    decompositions: dict[OpOverload, Callable[..., Any]] | None = None,
    ignore_shape_env: bool = False,
    compile_region_name: str | None = None,
) -> CompileFxOutput:
    """
    Main entry point for compiling given FX graph.  Despite the fact that this
    lives in :mod:`torch._inductor`, this function is responsible for calling
    into AOT Autograd (and we will eventually get a callback to
    ``inner_compile`` to perform actual compilation.  In other words, this
    function orchestrates end-to-end compilation for the inductor backend when
    you use :func:`torch.compile`.

    NB: This function TAKES OWNERSHIP of the input ``model_`` and can potentially
    mutate it!  Make a copy if you need to preserve the original GraphModule.
    """
    if decompositions is not None:

        def get_decomp_fn() -> dict[Any, Callable[..., Any]]:
            return decompositions  # pyrefly: ignore[bad-return]
    else:
        get_decomp_fn = select_decomp_table

    # Some arguments trigger a recursive call to compile_fx.  Handle these
    # short circuits first, before anything else

    from torch._inductor.compiler_bisector import CompilerBisector

    if CompilerBisector.disable_subsystem("inductor", "pre_grad_graph"):
        # pyrefly: ignore [bad-return]
        return model_

    if config_patches:
        with config.patch(config_patches):
            return compile_fx(
                model_,
                example_inputs_,
                # need extra layer of patching as backwards is compiled out of scope
                inner_compile=config.patch(config_patches)(inner_compile),
                decompositions=decompositions,
                ignore_shape_env=ignore_shape_env,
                compile_region_name=compile_region_name,
            )

    # Keep region names out of graph_kwargs so they don't perturb FX cache keys.
    inner_compile = functools.partial(
        inner_compile,
        compile_region_name=compile_region_name,
    )

    # Wake up the AsyncCompile subproc pool as early as possible (if there's cuda).
    if any(
        isinstance(e, torch.Tensor) and e.device.type in ("cuda", "xpu")
        for e in example_inputs_
    ):
        torch._inductor.async_compile.AsyncCompile.wakeup()

    if config.cpp_wrapper or config.fx_wrapper:
        from torch._export.non_strict_utils import _fakify_script_objects

        cpp_wrapper_config = config.cpp_wrapper
        fx_wrapper_config = config.fx_wrapper

        with (
            config.patch(get_cpp_wrapper_config()),
            V.set_real_inputs(example_inputs_),
        ):
            inputs_: Sequence[InputType] = (
                _extract_inputs_from_exported_gm(model_, example_inputs_)
                if isinstance(model_, GraphModule)
                else example_inputs_
            )
            fake_mode = detect_fake_mode(inputs_)
            with _fakify_script_objects(model_, inputs_, {}, fake_mode) as (
                patched_mod,
                fake_args,
                _,
                _,
                _,
            ):
                return _maybe_wrap_and_compile_fx_main(
                    patched_mod,
                    fake_args,
                    inner_compile=functools.partial(
                        inner_compile,
                        cpp_wrapper=cpp_wrapper_config,
                        fx_wrapper=fx_wrapper_config,
                    ),
                    ignore_shape_env=ignore_shape_env,
                    get_decomp_fn=get_decomp_fn,
                    compile_region_name=compile_region_name,
                )

    return _maybe_wrap_and_compile_fx_main(
        model_,
        example_inputs_,
        inner_compile,
        ignore_shape_env,
        get_decomp_fn=get_decomp_fn,
        compile_region_name=compile_region_name,
    )