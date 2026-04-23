def _aot_stage2b_compile_forward_or_inference(
    fw_module: torch.fx.GraphModule,
    adjusted_flat_args: list[Any],
    maybe_subclass_meta: SubclassMeta | None,
    fw_metadata: ViewAndMutationMeta,
    aot_config: AOTConfig,
    *,
    is_inference: bool,
    num_fw_outs_saved_for_bw: int | None = None,
    # pyrefly: ignore [implicit-any]
) -> tuple[list[tuple[int, ...] | None] | None, Callable]:
    """
    Compile the forward or inference graph. Returns:
    - the output strides of the forward graph
    - the compiled forward/inference function

    Args:
        fw_module: The forward graph module to compile
        adjusted_flat_args: Flattened arguments after adjustments
        maybe_subclass_meta: Metadata for tensor subclasses
        fw_metadata: View and mutation metadata
        aot_config: AOT configuration
        is_inference: If True, compile for inference; if False, compile for forward (autograd)
        num_fw_outs_saved_for_bw: Number of forward outputs saved for backward (required if not is_inference)

    Before compiling, we run pre_compile for the following wrappers:
    - FakifiedOutWrapper
    - FunctionalizedRngRuntimeWrapper
    After compiling, we run post_compile for the following wrappers:
    - EffectTokensWrapper
    - AOTDispatchSubclassWrapper
    - FunctionalizedRngRuntimeWrapper
    - FakifiedOutWrapper
    """

    # Validation
    if not is_inference and num_fw_outs_saved_for_bw is None:
        raise ValueError(
            "num_fw_outs_saved_for_bw must be provided when is_inference=False"
        )

    # Determine grad context, autocast context, tracking mode, compiler
    if is_inference:
        grad_ctx: Any = nullcontext
        autocast_ctx: Any = (
            torch._C._DisableAutocast
            if torch._C._is_any_autocast_enabled()
            else nullcontext
        )
        tracking_mode: str = "inference"
        compiler: Any = aot_config.inference_compiler
    else:
        grad_ctx = torch.no_grad
        autocast_ctx = torch._C._DisableAutocast
        tracking_mode = "forward"
        compiler = aot_config.fw_compiler

    with grad_ctx(), autocast_ctx(), track_graph_compiling(aot_config, tracking_mode):
        # Setup wrappers
        fakified_out_wrapper = FakifiedOutWrapper()
        fakified_out_wrapper.pre_compile(
            fw_module, adjusted_flat_args, aot_config, fw_metadata=fw_metadata
        )

        # Initialize RNG wrapper based on mode
        functionalized_rng_wrapper = FunctionalizedRngRuntimeWrapper(
            return_new_outs=is_inference
        )

        # Add RNG states for forward mode only
        if not is_inference and fw_metadata.num_graphsafe_rng_states > 0:
            index = fw_metadata.graphsafe_rng_state_index
            if index is None:
                raise AssertionError(
                    "fw_metadata.graphsafe_rng_state_index must not be None when num_graphsafe_rng_states > 0"
                )
            rng_states = [
                get_cuda_generator_meta_val(index)
                for _ in range(fw_metadata.num_graphsafe_rng_states)
            ]
            adjusted_flat_args.extend(rng_states)  # type: ignore[arg-type]

        functionalized_rng_wrapper.pre_compile(
            fw_module, adjusted_flat_args, aot_config, fw_metadata=fw_metadata
        )

        # Set tracing context
        if tracing_context := torch._guards.TracingContext.try_get():
            tracing_context.fw_metadata = _get_inner_meta(
                maybe_subclass_meta, fw_metadata
            )

        with TracingContext.report_output_strides() as fwd_output_strides:
            # pyrefly: ignore[not-callable]
            compiled_fw_func = compiler(fw_module, adjusted_flat_args)

        # Make boxed if needed
        if not getattr(compiled_fw_func, "_boxed_call", False):
            compiled_fw_func = make_boxed_func(compiled_fw_func)

        # Set forward output strides if needed
        if fakified_out_wrapper.needs_post_compile:
            fakified_out_wrapper.set_fwd_output_strides(fwd_output_strides)  # type: ignore[arg-type]

        # Apply post-compile wrappers
        compiled_fw_func = EffectTokensWrapper().post_compile(
            compiled_fw_func,
            aot_config,
            runtime_metadata=fw_metadata,
        )

        compiled_fw_func = AOTDispatchSubclassWrapper(
            fw_only=None,
            trace_joint=False,
            maybe_subclass_meta=maybe_subclass_meta,
            num_fw_outs_saved_for_bw=num_fw_outs_saved_for_bw,
        ).post_compile(
            compiled_fw_func,
            aot_config,
            runtime_metadata=fw_metadata,
        )

        compiled_fw_func = functionalized_rng_wrapper.post_compile(
            compiled_fw_func, aot_config, runtime_metadata=fw_metadata
        )

        compiled_fw_func = fakified_out_wrapper.post_compile(
            compiled_fw_func,
            aot_config,
            runtime_metadata=fw_metadata,
        )

        return fwd_output_strides, compiled_fw_func