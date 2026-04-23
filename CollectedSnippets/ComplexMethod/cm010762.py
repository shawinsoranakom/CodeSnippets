def aot_module_simplified(
    mod: torch.fx.GraphModule | torch._dynamo.utils.GmWrapper,
    args: Sequence[Any],
    fw_compiler: AOTDispatchCompiler,
    bw_compiler: AOTDispatchCompiler | None = None,
    partition_fn: Callable[..., Any] = default_partition,
    decompositions: dict[OpOverload, Callable[..., Any]] | None = None,
    keep_inference_input_mutations: bool = False,
    inference_compiler: AOTDispatchCompiler | None = None,
    # TODO: This doesn't seem to be used in any nontrivial way, check if it's
    # actually needed
    compiler_config_extra: CompilerConfigExtra | None = None,
    ignore_shape_env: bool = False,
    disable_functionalization: bool = False,
    # Optional callback to run passes on the module at the start of AOT autograd.
    pre_grad_passes: Callable[
        [torch.fx.GraphModule, Sequence[InputType]], torch.fx.GraphModule
    ]
    | None = None,
    compile_region_name: str | None = None,
) -> Callable[..., Any]:
    """
    This is the simplified or low overhead version of aot_module. For frontends
    like TorchDynamo, the input functions/modules to AOT are static and have
    unpacked inputs/outputs. This gives us an opportunity to remove the
        (1) pytree overhead to parse inputs/outputs,
        (2) AOT Autograd cache,
        (3) Reading of params/buffers in every forward call

    :func:`aot_module_simplified` removes these overheads.
    """

    pre_grad_pass_timing: Literal["early", "late"] = resolve_pre_grad_pass_timing()

    if (
        pre_grad_pass_timing == "early"
        and pre_grad_passes
        and isinstance(mod, torch.fx.GraphModule)
    ):
        mod = pre_grad_passes(mod, args)

    with contextlib.ExitStack() as stack:
        (
            functional_call,
            params_buffers_flat,
            _params_spec,
            _buffers_spec,
            fake_flat_args,
            full_args_descs,
            aot_config,
            fake_mode,
            shape_env,
            _in_spec,
            _out_spec,
            act_input_indices,
        ) = prepare_aot_module_simplified(
            mod,
            args,
            None,
            decompositions,
            keep_inference_input_mutations,
            ignore_shape_env,
            flatten=False,
            force_non_lazy_backward_lowering=config.force_non_lazy_backward_lowering,
            disable_functionalization=disable_functionalization,
        )

        compiled_fn = None

        if (
            isinstance(fw_compiler, SerializableAOTDispatchCompiler)
            or torch._functorch.config.force_autograd_cache
        ):
            local = should_use_local_autograd_cache()
            remote = should_use_remote_autograd_cache()
            if local or remote:
                set_feature_use("aot_autograd_remote_cache", remote)
                compiled_fn = AOTAutogradCache.try_load(
                    mod,
                    fake_flat_args,
                    aot_config,
                    compiler_config_extra,
                    local,
                    remote,
                    compile_region_name=compile_region_name,
                )

        if compiled_fn is None:
            if (
                pre_grad_pass_timing == "late"
                and pre_grad_passes
                and isinstance(mod, torch.fx.GraphModule)
            ):
                mod = pre_grad_passes(mod, args)

            stack.enter_context(compiled_autograd._disable())
            aot_state = create_aot_state(
                stack,
                functional_call,
                fake_flat_args,
                full_args_descs,
                aot_config,
                fake_mode,
                shape_env,
            )
            aot_state.fw_metadata.act_input_indices = act_input_indices
            aot_graph_capture = aot_stage1_graph_capture(aot_state, functional_call)
            compiled_fn, _ = aot_stage2_compile(
                aot_state,
                aot_graph_capture,
                partition_fn,
                fw_compiler,
                bw_compiler,
                inference_compiler,
            )
    if compiled_fn is None:
        raise AssertionError("compiled_fn must not be None")
    if isinstance(mod, torch._dynamo.utils.GmWrapper):
        # This function is called by the flatten_graph_inputs wrapper, which boxes
        # the inputs so that they can be freed before the end of this scope.
        # For overhead reasons, this is not the default wrapper, see comment:
        # https://github.com/pytorch/pytorch/pull/122535/files#r1560096481
        @simple_wraps(compiled_fn)
        def forward(runtime_args: list[Any]) -> Any:
            flat_args = []
            flat_args.extend(params_buffers_flat)
            flat_args.extend(runtime_args)
            runtime_args.clear()
            if compiled_fn is None:
                raise AssertionError("compiled_fn must not be None")
            return compiled_fn(flat_args)

    else:
        # TODO: There is something deeply wrong here; compiled_fn running with
        # the boxed calling convention, but aot_module_simplified somehow
        # historically returned a function that was not the boxed calling
        # convention.  This should get fixed...
        # NB: GraphModule/nn.Module rely on the non-boxed calling convention here
        @simple_wraps(compiled_fn)
        def forward(*runtime_args: tuple[Any]) -> Any:
            full_args = []
            full_args.extend(params_buffers_flat)
            # pyrefly: ignore[bad-argument-type]
            full_args.extend(runtime_args)
            if compiled_fn is None:
                raise AssertionError("compiled_fn must not be None")
            return compiled_fn(full_args)

    # Just for convenience
    forward.zero_grad = mod.zero_grad  # type: ignore[attr-defined]
    forward.named_parameters = mod.named_parameters  # type: ignore[attr-defined]
    forward.named_buffers = mod.named_buffers  # type: ignore[attr-defined]

    # Add a serialize function
    def grab_serialize_fn(fn: Any) -> Callable[..., Any] | None:
        if isinstance(fn, SerializableCompiledFunction):
            return fn.serialize_fn
        elif hasattr(fn, "__wrapped__"):
            return grab_serialize_fn(fn.__wrapped__)
        else:
            return None

    forward.serialize = grab_serialize_fn(forward)  # type: ignore[attr-defined]
    return forward