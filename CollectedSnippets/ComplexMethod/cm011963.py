def _compile_fx_main(
    model_: GraphModule,
    example_inputs_: Sequence[InputType],
    inner_compile: Callable[..., OutputCode],
    ignore_shape_env: bool,
    *,
    get_decomp_fn: Callable[..., dict[Any, Callable[..., Any]]] = select_decomp_table,
    compile_region_name: str | None = None,
) -> CompileFxOutput:
    """
    Main part of compile_fx, called after wrapping is done.

    Roughly speaking, here the steps will be:
    (1) apply pre-grad passes
    (2) create `fw_compiler` and `bw_compiler` functions out of `inner_compile`
    (3) call aot_autograd, which:
    - (3a) creates a joint graph with `decompositions`,
    - (3b) partitions it with `partition_fn` into fw and bw graphs (applying joint-graph passes),
    - (3c) calls `fw_compiler` and `bw_compiler` on those graphs (applying post-grad passes)
    - (3d) finally, assembles the fw and bw compiled functions back together and returns.
    """
    with (
        _use_lazy_graph_module(dynamo_config.use_lazy_graph_module),
        enable_python_dispatcher(),
        torch.fx.traceback.preserve_node_meta(
            config.trace.provenance_tracking_level == 1
        ),
        torch._inductor.debug.reset_provenance_globals(),
    ):
        # Note: Pre-grad passes are now run inside aot_module_simplified (via the
        # pre_grad_passes callback) after the cache lookup.

        assert not config._raise_error_for_testing

        num_example_inputs = len(example_inputs_)

        compiler_config_extra = create_compiler_config_extra(model_)

        decompositions = get_decomp_fn()
        inner_compile = functools.partial(inner_compile, get_decomp_fn=get_decomp_fn)

        def fw_compiler_base(
            gm: GraphModule,
            example_inputs: Sequence[InputType],
            is_inference: bool,
        ) -> OutputCode:
            with dynamo_utils.dynamo_timed("compile_fx.<locals>.fw_compiler_base"):
                if isinstance(model_, GraphModule):
                    num_orig_model_outputs = get_num_model_outputs(model_)
                else:
                    num_orig_model_outputs = get_num_model_outputs(gm)
                return compile_fx_forward(
                    gm,
                    example_inputs,
                    num_orig_model_outputs=num_orig_model_outputs,
                    num_example_inputs=num_example_inputs,
                    compiler_config_extra=compiler_config_extra,
                    inner_compile=inner_compile,
                    is_inference=is_inference,
                )

        fw_compiler: Callable[[GraphModule, Sequence[InputType]], OutputCode] = (
            functools.partial(fw_compiler_base, is_inference=False)
        )
        fw_compiler = SerializableAOTDispatchCompiler(OutputCode, fw_compiler)

        if config.freezing and not torch.is_grad_enabled():
            inference_compiler: Callable[..., Any] = functools.partial(
                fw_compiler_freezing,
                dynamo_model=model_,
                num_example_inputs=num_example_inputs,
                inner_compile=inner_compile,
                cudagraphs=compiler_config_extra.cudagraphs,
                graph_id=compiler_config_extra.graph_id,
                forward_device=compiler_config_extra.forward_device,
            )
        else:
            inference_compiler = functools.partial(fw_compiler_base, is_inference=True)
            inference_compiler = SerializableAOTDispatchCompiler(
                OutputCode, inference_compiler
            )

        @compile_time_strobelight_meta(phase_name="backward")
        def bw_compiler(
            gm: GraphModule, example_inputs: Sequence[InputType]
        ) -> OutputCode:
            with (
                dynamo_utils.dynamo_timed("compile_fx.<locals>.bw_compiler"),
            ):
                return compile_fx_backward(
                    gm,
                    example_inputs,
                    compiler_config_extra=compiler_config_extra,
                    inner_compile=inner_compile,
                )

        bw_compiler = SerializableAOTDispatchCompiler(OutputCode, bw_compiler)

        fake_mode = detect_fake_mode(
            example_inputs_
        ) or torch._subclasses.FakeTensorMode(allow_non_fake_inputs=True)
        tracing_context = (
            torch._guards.TracingContext.try_get()
            or torch._guards.TracingContext(fake_mode)
        )

        if V.aot_compilation and not config.enable_autograd_for_aot:
            from .utils import is_valid_aoti_model_name

            is_valid_aoti_model_name()

            # Pre-grad passes for the aot_autograd path are run inside
            # aot_module_simplified after the cache lookup.  The
            # aot_export_module path doesn't use that cache so run them here.
            if isinstance(model_, GraphModule):
                model_ = run_pre_grad_passes(model_, example_inputs_)

            with functorch_config.patch(
                unlift_effect_tokens=True,
                selective_decompose=config.selective_decompose,
            ):
                gm, graph_signature = aot_export_module(
                    model_,
                    example_inputs_,
                    trace_joint=False,
                    decompositions=decompositions,
                )
                assert isinstance(gm, GraphModule)
                from torch._export.utils import _detect_fake_mode_from_gm

                fake_mode = _detect_fake_mode_from_gm(gm)  # type: ignore[assignment]
                # aot_export_module doesn't account for constant tensor attributes
                # so we end up having tensors that don't have fake vals attached.
                # This can happen when upstream export is non-strict where we
                # preserve the original module params/buffers. Once AOTI switches
                # to ep.run_decompositions() flow to lower to post-autograd opset
                # this will go away.
                for node in gm.graph.nodes:
                    if node.op == "get_attr" and "val" not in node.meta:
                        target = attrgetter(node.target)(gm)
                        if isinstance(target, torch.Tensor):
                            assert fake_mode is not None
                            node.meta["val"] = fake_mode.from_tensor(
                                target, static_shapes=True
                            )
                        elif isinstance(target, torch.ScriptObject) or is_opaque_type(
                            type(target)
                        ):
                            node.meta["val"] = (
                                torch._library.fake_class_registry.maybe_to_fake_obj(
                                    fake_mode, target
                                )
                            )
                        elif isinstance(target, FakeScriptObject):
                            node.meta["val"] = target

            unlifted_gm = _unlift_graph(model_, gm, graph_signature)
            if "dynamo_flat_name_to_original_fqn" in model_.meta:
                unlifted_gm.meta["dynamo_flat_name_to_original_fqn"] = model_.meta[
                    "dynamo_flat_name_to_original_fqn"
                ]

            if "dynamo_compile_id" in model_.meta:
                unlifted_gm.meta["dynamo_compile_id"] = model_.meta["dynamo_compile_id"]

            # Disable amp as in aot_dispatch_autograd (https://github.com/pytorch/pytorch/pull/86515)
            # In inference_compiler (fw_compiler_base), _recursive_joint_graph_passes will call into
            # _sfdp_init() to register patterns.
            # When fallback_random is set to True, the sdpa patterns will be traced during runtime.
            # If amp is turned on, the traced FP32 patterns will have prims.convert_element_type which
            # will be the same as the generated FP16 patterns.
            disable_amp = torch._C._is_any_autocast_enabled()
            context = (
                torch._C._DisableAutocast if disable_amp else contextlib.nullcontext
            )
            with V.set_fake_mode(fake_mode), compiled_autograd._disable(), context():
                return inference_compiler(unlifted_gm, example_inputs_)

        with (
            V.set_fake_mode(fake_mode),
            torch._guards.tracing(tracing_context),
            compiled_autograd._disable(),
            functorch_config.patch(
                unlift_effect_tokens=True,
                selective_decompose=config.selective_decompose,
            ),
        ):
            try:
                return dynamo_common.aot_autograd(
                    fw_compiler=fw_compiler,
                    bw_compiler=bw_compiler,
                    inference_compiler=inference_compiler,
                    decompositions=decompositions,
                    partition_fn=partition_fn,
                    keep_inference_input_mutations=True,
                    compiler_config_extra=compiler_config_extra,
                    ignore_shape_env=ignore_shape_env,
                    pre_grad_passes=run_pre_grad_passes,
                    compile_region_name=compile_region_name,
                )(model_, example_inputs_)
            except ShortenTraceback as e:
                # We will also shorten the traceback inside dynamo.
                # This is only useful if inductor is called directly with an FX graph.
                raise e.remove_dynamo_frames() from None