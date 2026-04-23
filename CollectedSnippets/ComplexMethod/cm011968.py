def codegen_and_compile(
        self,
        gm: GraphModule,
        example_inputs: Sequence[InputType],
        inputs_to_check: Sequence[int],
        graph_kwargs: _CompileFxKwargs,
    ) -> OutputCode:
        """
        Generates the OutputCode from the GraphModule and example_inputs.
        """
        # Sorry about the mess, we need graph_kwargs to continue to be able
        # to propagate it further on
        # TODO: _CompileFxKwargs actually has stronger types than in the
        # signature, need to tighten it up

        assert "cudagraphs" in graph_kwargs and graph_kwargs["cudagraphs"] is not None
        cudagraphs: BoxedBool = graph_kwargs["cudagraphs"]
        static_input_idxs: Sequence[int] = graph_kwargs.get("static_input_idxs", ())
        is_backward: bool = graph_kwargs.get("is_backward", False)
        graph_id: int | None = graph_kwargs.get("graph_id", None)
        cpp_wrapper: bool = graph_kwargs.get("cpp_wrapper", False)
        fx_wrapper: bool = graph_kwargs.get("fx_wrapper", False)
        aot_mode: bool = V.aot_compilation
        is_inference: bool = graph_kwargs.get("is_inference", False)
        extern_node_serializer: Callable[[list[ExternKernelNode]], Any] | None = (
            graph_kwargs.get("extern_node_serializer", None)
        )
        get_decomp_fn: Callable[..., dict[Any, Callable[..., Any]]] = graph_kwargs.get(
            "get_decomp_fn", select_decomp_table
        )
        with (
            _WaitCounter("pytorch.wait_counter.actual_codegen_and_compile").guard(),
            dynamo_utils.preserve_rng_state(),
        ):
            if (sleep_sec := config.sleep_sec_TESTING_ONLY) is not None:
                import time

                log.warning(
                    "Sleeping for %s since sleep_sec_TESTING_ONLY is set", sleep_sec
                )
                time.sleep(sleep_sec)

            if is_tf32_warning_applicable(gm):
                _warn_tf32_disabled()

            inductor_counters = counters["inductor"].copy()

            # lift the maximum depth of the Python interpreter stack
            # to adapt large/deep models
            sys.setrecursionlimit(max(sys.getrecursionlimit(), 2000))

            _step_logger()(
                logging.INFO,
                "torchinductor compiling "
                f"{'BACKWARDS' if is_backward else 'FORWARDS'} "
                f"graph {graph_id}",
            )

            fd = io.StringIO()
            torch._dynamo.repro.after_aot.save_graph_repro(
                fd, gm, example_inputs, "inductor", save_dir=None
            )
            runnable_graph_str = fd.getvalue()

            trace_structured(
                "artifact",
                metadata_fn=lambda: {
                    "name": "fx_graph_runnable",
                    "encoding": "string",
                },
                payload_fn=lambda: runnable_graph_str,
            )

            V.debug.fx_graph(gm, example_inputs)
            # TODO: Should we actually dump this?  It should be redundant with the aot
            # structured logs...
            # trace_structured("inductor_input_graph", payload_fn=lambda: gm.print_readable(print_output=False))

            shape_env = gm.shape_env
            if shape_env is None:
                shape_env = shape_env_from_inputs(example_inputs)

            # Convert view to reshape in the graph. This is necessary primarily for
            # layout optimization. Do it unconditionally for uniformity.
            #
            # It's needed because when we do layout optimization, an contiguous tensor
            # in eager mode may becomes a channels last tensor. A view op previously
            # can be applied to the contiguous tensor may not be able to be applied
            # on the channels tensor any more. An error like
            #   RuntimeError: view size is not compatible with input tensor's size and stride
            #   (at least one dimension spans across two contiguous subspaces). Use .reshape(...) instead.
            # will be printed.
            #
            # Replace view op to reshape op in this case.
            # As an example, timm_resnest/botnet26t_256/convnext_base etc. will fail if we don't do this.
            #
            # Also this has to be done before FakeTensorProp below to avoid the failed
            # .view() call.
            view_to_reshape(gm)

            with dynamo_timed(
                "additional_fake_tensor_prop", log_pt2_compile_event=True
            ):
                # It is safe to run FakeTensorProp under no_grad because by the time
                # we're in inductor, we assume that AOTAutograd has already "taken care"
                # of autograd, so there should be no more autograd-related API's in the
                # graph.
                with torch.no_grad():
                    fake_mode = fake_tensor_prop(gm, example_inputs)

            _recursive_record_original_output_strides(gm)

            # pattern matcher passes might not preserve striding information
            # on node.meta["val"]. if in the future we rely on these being
            # correct we will need to fix.
            trace_structured(
                "artifact",
                metadata_fn=lambda: {
                    "name": "before_post_grad_graph",
                    "encoding": "string",
                },
                payload_fn=lambda: gm.print_readable(
                    print_output=False, include_stride=True, include_device=True
                ),
            )
            with V.set_fake_mode(fake_mode):
                # has some issues with memory in training
                cuda_context = get_cuda_device_context(gm)
                with cuda_context:
                    _recursive_post_grad_passes(gm, is_inference=is_inference)
                V.debug.fx_graph_transformed(gm, example_inputs)
                post_grad_graphs_log.debug(
                    "%s",
                    lazy_format_graph_code(
                        "AFTER POST GRAD",
                        gm,
                        include_stride=True,
                        include_device=True,
                        colored=True,
                    ),
                )

                # We're printing the graph to be used as a cache key - so a
                # printer which is a little less readable but faster is
                # appropriate.
                inductor_post_grad_graph_str = gm.print_readable(
                    print_output=False,
                    include_stride=True,
                    include_device=True,
                    fast_sympy_print=True,
                )
                # "inductor_post_grad_graph" is used in inductor provenance
                # tracking highlighter front-end.
                trace_structured(
                    "artifact",
                    metadata_fn=lambda: {
                        "name": "inductor_post_grad_graph",
                        "encoding": "string",
                    },
                    payload_fn=lambda: inductor_post_grad_graph_str,
                )
                if config.trace.provenance_tracking_level != 0:
                    provenance_tracking_json = (
                        torch.fx.traceback.get_graph_provenance_json(gm.graph)
                    )
                    torch._inductor.debug._inductor_post_to_pre_grad_nodes = (
                        create_mapping_pre_post_grad_nodes(
                            torch._inductor.debug._pre_grad_graph_id,
                            provenance_tracking_json,
                        )
                    )

                metrics_context = get_metrics_context()
                if metrics_context.in_progress():
                    num_graph_breaks = counters["graph_break"].total()
                    CompileEventLogger.compilation_metric(
                        overwrite=True, num_graph_breaks=num_graph_breaks
                    )
                if config.is_fbcode():
                    try:
                        log_optimus_to_scuba(
                            extra_logging={
                                "pt2_configs": str(get_patched_config_dict())
                            }
                        )
                    except Exception:
                        # TODO(T216453900): need to work around for now to support vllm
                        # See details in vllm/compilation/pass_manager.py.
                        log.warning("failed to log pt2_configs")

            with (
                V.set_fake_mode(fake_mode),
                maybe_disable_comprehensive_padding(example_inputs),
                maybe_disable_graph_partition(cpp_wrapper, aot_mode),
            ):
                const_output_index = None
                const_graph = None
                const_wrapper_code = None
                const_kernel_code = None

                if aot_mode and config.aot_inductor.use_runtime_constant_folding:
                    # torchbind objects have name that starts with _torchbind_obj
                    # See caffe2/torch/fx/_symbolic_trace.py?lines=406
                    const_gm, const_output_index = split_const_gm(
                        gm,
                        skip_folding_node_fn=lambda node: node.op == "get_attr"
                        and isinstance(node.target, str)
                        and (
                            node.target.startswith("_torchbind_obj")
                            or isinstance(node.meta.get("val", None), FakeScriptObject)
                        ),
                    )

                    const_graph = GraphLowering(
                        const_gm,
                        example_inputs=[],
                        shape_env=shape_env,
                        graph_id=graph_id,
                        cpp_wrapper=cpp_wrapper,
                        aot_mode=aot_mode,
                        extern_node_serializer=extern_node_serializer,
                        is_inference=is_inference,
                        is_backward=is_backward,
                        is_const_graph=True,
                        fx_wrapper=fx_wrapper,
                        get_decomp_fn=get_decomp_fn,
                    )
                    with (
                        V.set_graph_handler(const_graph),
                        V.set_extern_kernel_nodes([]),
                    ):
                        assert cpp_wrapper, "AOT mode only supports C++ wrapper"
                        const_graph.run()
                        const_wrapper_code, const_kernel_code = (
                            const_graph.codegen_with_cpp_wrapper()
                        )

                graph = GraphLowering(
                    gm,
                    # example_inputs will be used by AOTInductor to dry-run the generated code for Triton kernel tuning.
                    # For the forward pass, we have the real inputs to be used as example_inputs. For the backward pass,
                    # we currently use fake tensors and defake them later.
                    example_inputs=example_inputs,
                    shape_env=shape_env,
                    graph_id=graph_id,
                    cpp_wrapper=cpp_wrapper,
                    aot_mode=aot_mode,
                    extern_node_serializer=extern_node_serializer,
                    is_inference=is_inference,
                    is_backward=is_backward,
                    const_output_index=const_output_index,
                    const_wrapper_code=(
                        const_wrapper_code.value if const_wrapper_code else None
                    ),
                    const_kernel_code=(
                        const_kernel_code.value if const_kernel_code else None
                    ),
                    const_module=const_graph,
                    inputs_to_check=inputs_to_check,
                    fx_wrapper=fx_wrapper,
                    get_decomp_fn=get_decomp_fn,
                )
                metrics_helper = metrics.CachedMetricsHelper()

                # We are going to start code generating runtime asserts, so make sure
                # you don't start adding new ones in the lowering process
                graph.freeze_runtime_asserts()
                with (
                    V.set_graph_handler(graph),
                    V.set_extern_kernel_nodes([]),
                    distributed_autotune.graph_context(),
                ):
                    graph.run(*example_inputs)
                    output_strides: list[tuple[_StrideExprStr, ...] | None] = []
                    if graph.graph_outputs is not None:
                        # We'll put the output strides in the compiled graph so we
                        # can later return them to the caller via TracingContext
                        p = SymExprPrinter()
                        for out in graph.graph_outputs:
                            if (
                                isinstance(out, IRNode)
                                and out.has_tensor_output()
                                and len(free_unbacked_symbols(out.get_stride())) == 0
                            ):
                                # Convert to string for eval on the load path
                                output_strides.append(
                                    tuple(p.doprint(s) for s in out.get_layout().stride)
                                )
                            else:
                                output_strides.append(None)

                    _check_triton_bf16_support(graph)

                    # TODO: The switching between AOT mode and not here is a bit
                    # messy, but it's localized to the block of code below so I'm
                    # not going to touch it for now

                    compiled_fn: Any
                    compiled_fn_runner = None
                    with dynamo_timed(
                        "GraphLowering.compile_to_fn", log_pt2_compile_event=True
                    ):
                        if graph.aot_mode and graph.fx_wrapper:
                            assert not graph.cpp_wrapper
                            compiled_fn = graph.codegen()[0].gm  # type: ignore[attr-defined]
                            output_code_log.debug(
                                "Output graph module: \n%s",
                                compiled_fn.print_readable(print_output=False),
                            )

                        elif graph.aot_mode:
                            from .codecache import AotCodeCompiler

                            assert graph.cpp_wrapper, (
                                "AOT mode only supports C++ wrapper"
                            )
                            wrapper_code, kernel_code = graph.codegen_with_cpp_wrapper()
                            output_code_log.debug(
                                "Output wrapper code: \n%s", wrapper_code.value
                            )
                            if kernel_code.value:
                                output_code_log.debug(
                                    "Output kernel code:\n%s", kernel_code.value
                                )

                            serialized_extern_kernel_nodes = None
                            if V.extern_kernel_nodes:
                                serialized_extern_kernel_nodes = (
                                    graph.extern_node_serializer(V.extern_kernel_nodes)
                                )
                                output_code_log.debug(
                                    "Serialized Extern Kernel Nodes: \n%s",
                                    serialized_extern_kernel_nodes,
                                )

                            with dynamo_timed(
                                "AotCodeCompiler.compile", log_pt2_compile_event=True
                            ):
                                # Directly return the file path with the compiled code
                                compiled_fn = AotCodeCompiler.compile(
                                    graph,
                                    wrapper_code.value,
                                    kernel_code.value,
                                    serialized_extern_kernel_nodes,
                                    device_type=graph.device_type,
                                    additional_files=[
                                        *dict.fromkeys(
                                            graph.wrapper_code.additional_files
                                            + (
                                                const_graph.wrapper_code.additional_files
                                                if const_graph
                                                else []
                                            )
                                        )
                                    ],
                                )
                        else:
                            compiled_module = graph.compile_to_module()
                            compiled_fn = compiled_module.call
                            compiled_fn_runner = getattr(
                                compiled_module, "runner", None
                            )

                    # Dump provenance artifacts for debugging trace
                    inductor_provenance_tracking_node_mappings = None
                    inductor_kernel_stack_trace_str = None
                    if config.trace.provenance_tracking_level != 0:
                        inductor_provenance_tracking_node_mappings = json.dumps(
                            torch._inductor.debug.dump_inductor_provenance_info()
                        )
                        inductor_kernel_stack_trace_str = json.dumps(
                            torch._inductor.debug._inductor_kernel_stack_trace
                        )
                        trace_structured(
                            "artifact",
                            metadata_fn=lambda: {
                                "name": "inductor_provenance_tracking_node_mappings",
                                "encoding": "json",
                            },
                            payload_fn=lambda: inductor_provenance_tracking_node_mappings,
                        )
                        trace_structured(
                            "artifact",
                            metadata_fn=lambda: {
                                "name": "inductor_provenance_tracking_kernel_stack_traces",
                                "encoding": "json",
                            },
                            payload_fn=lambda: inductor_kernel_stack_trace_str,
                        )
                        if inductor_kernel_stack_trace_str:
                            metrics_context = get_metrics_context()
                            if metrics_context.in_progress():
                                metrics_context.add_to_set(
                                    "inductor_provenance",
                                    inductor_kernel_stack_trace_str,
                                )

                    node_runtimes = None
                    if inductor_metrics_log.isEnabledFor(logging.INFO):
                        num_bytes, nodes_num_elem, node_runtimes = graph.count_bytes()
                        # pyrefly: ignore [bad-assignment]
                        metrics.num_bytes_accessed += num_bytes
                        metrics.node_runtimes += node_runtimes
                        metrics.nodes_num_elem += nodes_num_elem
                        inductor_metrics_log.info(
                            "Graph Metrics:\n%s",
                            {
                                "num_bytes_accessed": num_bytes,
                                "nodes_num_elem": nodes_num_elem,
                                "node_runtimes": node_runtimes,
                            },
                        )

                    # Collect and dump op runtimes and tensor metadata for TLParse
                    if config.log_tlparse:
                        _, _, node_runtimes = graph.count_bytes()
                        torch._inductor.debug.log_runtime_and_tensor_meta(node_runtimes)

                    # Collect and dump collective-op schedule for external diagnostics
                    torch._inductor.debug.log_collective_schedule(graph.scheduler.nodes)

                    # When graph_partition is enabled, skip this check - partitioning handles dynamic shapes
                    if (
                        cudagraphs
                        and config.triton.cudagraph_skip_dynamic_graphs
                        and not config.graph_partition
                        and not V.graph.disable_cudagraphs_reason
                        and torch._inductor.utils.any_is_symbolic(*example_inputs)
                    ):
                        stack_trace = None
                        for node in gm.graph.nodes:
                            meta_val = node.meta.get("val", None)
                            if (
                                node.op == "placeholder"
                                or not isinstance(meta_val, torch.Tensor)
                                or not torch._inductor.utils.any_is_symbolic(meta_val)
                            ):
                                continue

                            if stack_trace := node.meta.get("stack_trace", None):
                                break
                        disable = "graph with symbolic shapes inputs and config.triton.cudagraph_skip_dynamic_graphs=True."
                        if stack_trace:
                            disable = f"{disable} Found from {stack_trace}\n"
                        else:
                            disable = f"{disable}\n"
                        # pyrefly: ignore [unbound-name]
                        V.graph.disable_cudagraphs_reason = disable

                    # pyrefly: ignore [unbound-name]
                    # When graph_partition is enabled, skip this check - partitioning handles incompatible ops
                    if (
                        cudagraphs
                        # pyrefly: ignore [unbound-name]
                        and not config.graph_partition
                        # pyrefly: ignore [unbound-name]
                        and not V.graph.disable_cudagraphs_reason
                    ):
                        maybe_incompat_node = get_first_incompatible_cudagraph_node(gm)
                        if maybe_incompat_node:
                            disable = f"disabling cudagraphs due to incompatible op {maybe_incompat_node.target}"
                            if stack_trace := maybe_incompat_node.meta.get(
                                "stack_trace", None
                            ):
                                disable = f"{disable} Found from {stack_trace}\n"
                            # pyrefly: ignore [unbound-name]
                            V.graph.disable_cudagraphs_reason = disable

                    # pyrefly: ignore [unbound-name]
                    if V.aot_compilation:
                        assert isinstance(
                            compiled_fn,
                            # pyrefly: ignore [unbound-name]
                            (str, list, torch.fx.GraphModule),
                        ), type(compiled_fn)
                        return CompiledAOTI(
                            filename=compiled_fn, device_type=graph.device_type
                        )

                    # TODO: Hoist this above V.aot_compilation
                    # pyrefly: ignore [unbound-name]
                    if cudagraphs and not V.graph.disable_cudagraphs_reason:
                        from torch._inductor.cudagraph_utils import (
                            check_lowering_disable_cudagraph,
                        )

                        # pyrefly: ignore [unbound-name]
                        V.graph.disable_cudagraphs_reason = (
                            check_lowering_disable_cudagraph(
                                # pyrefly: ignore [unbound-name]
                                V.graph.device_node_mapping
                            )
                        )

                    self._compile_stats[type(self)].codegen_and_compile += 1

                    if (
                        # pyrefly: ignore [unbound-name]
                        torch._inductor.debug.RECORD_GRAPH_EXECUTION
                        # pyrefly: ignore [unbound-name]
                        and torch._inductor.debug.GRAPH_COMPILE_IDS is not None
                    ):
                        compile_id = str(
                            # pyrefly: ignore [unbound-name]
                            torch._guards.CompileContext.current_compile_id()
                        )
                        graph_id = graph_kwargs.get("graph_id")
                        if graph_id is not None:
                            # pyrefly: ignore [unbound-name]
                            torch._inductor.debug.GRAPH_COMPILE_IDS[graph_id] = (
                                compile_id
                            )

                    return CompiledFxGraph(
                        compiled_fn,
                        graph,
                        gm,
                        output_strides,
                        # pyrefly: ignore [unbound-name]
                        V.graph.disable_cudagraphs_reason,
                        metrics_helper.get_deltas(),
                        counters["inductor"] - inductor_counters,
                        cudagraphs,
                        example_inputs,
                        static_input_idxs,
                        self.compile_region_name,
                        graph_kwargs,
                        inputs_to_check,
                        runnable_graph_str,
                        inductor_post_grad_graph_str,
                        compiled_fn_runner,
                        inductor_provenance_tracking_node_mappings,
                        inductor_kernel_stack_trace_str,
                    )