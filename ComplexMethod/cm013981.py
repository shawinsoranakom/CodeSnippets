def _compile(
    code: CodeType,
    globals: dict[str, object],
    locals: dict[str, object],
    builtins: dict[str, object],
    closure: tuple[CellType],
    compiler_fn: CompilerFn,
    one_graph: bool,
    export: bool,
    export_constraints: Any | None,
    hooks: Hooks,
    cache_entry: CacheEntry | None,
    cache_size: CacheSizeRelevantForFrame,
    frame: DynamoFrameType | None = None,
    frame_state: dict[str, int | FrameStateSizeEntry] | None = None,
    *,
    compile_id: CompileId,
    skip: int = 0,
    package: CompilePackage | None = None,
    # Can be used to record things for the caller, both
    # in the case of normal and exception code paths
    convert_frame_box: ConvertFrameBox | None = None,
) -> ConvertFrameReturn:
    from torch.fx.experimental.validator import (
        BisectValidationException,
        ValidationException,
    )

    # Only nonlocal defs here please!
    # Time spent compiling this frame before restarting or failing analysis
    dynamo_time_before_restart: float = 0.0

    @compile_time_strobelight_meta(phase_name="compile_inner")
    def compile_inner(
        code: CodeType, one_graph: bool, hooks: Hooks
    ) -> tuple[ConvertFrameReturn, DynamoTracerOutput | None]:
        with contextlib.ExitStack() as stack:
            stack.enter_context(
                torch._dynamo.callback_handler.install_callbacks(
                    CallbackTrigger.DYNAMO, str(CompileContext.current_compile_id())
                )
            )
            stack.enter_context(CompileTimeInstructionCounter.record())
            stack.enter_context(torch_function_mode_stack_state_mgr)
            result = _compile_inner(code, one_graph, hooks)
            assert torch._C._len_torch_function_stack() == 0, (
                "Torch function mode stack state changed while dynamo tracing, please report a bug"
            )
            return result

        return (
            ConvertFrameReturn(),
            None,
        )  # dead, but see https://github.com/python/mypy/issues/7577

    @maybe_cprofile
    def _compile_inner(
        code: CodeType,
        one_graph: bool,
        hooks: Hooks,
    ) -> tuple[ConvertFrameReturn, DynamoTracerOutput]:
        nonlocal dynamo_time_before_restart
        last_attempt_start_time = start_time = time.time()

        def log_bytecode(
            prefix: str, name: str, filename: str, line_no: int, code: CodeType
        ) -> None:
            if bytecode_log.isEnabledFor(logging.DEBUG):
                bytecode_log.debug(
                    format_bytecode(prefix, name, filename, line_no, code)
                )

        log_bytecode(
            "ORIGINAL BYTECODE",
            code.co_name,
            code.co_filename,
            code.co_firstlineno,
            code,
        )
        # Dump the ORIGINAL bytecode of resumption frame into TORCH_TRACE
        # log file, so that it is parsed by tlparse tool.
        is_resumption_frame = "torch_dynamo_resume_in" in code.co_name
        if is_resumption_frame:
            torch._logging.trace_structured(
                "artifact",
                metadata_fn=lambda: {
                    "name": code.co_name + "_ORIGINAL_BYTECODE",
                    "encoding": "string",
                },
                payload_fn=lambda: dis.Bytecode(code).dis(),
            )
        out_code = None
        from .graph_id_filter import get_dynamo_config_override_for_compile_id

        dynamo_config_override = get_dynamo_config_override_for_compile_id(
            compile_id, config.debug_dynamo_config_override
        )
        try:
            with (
                config.patch(dynamo_config_override)
                if dynamo_config_override
                else contextlib.nullcontext()
            ):
                dynamo_output = compile_frame(
                    code,
                    globals,
                    locals,
                    builtins,
                    closure,
                    compiler_fn,
                    one_graph,
                    restart_reasons,
                    export=export,
                    export_constraints=export_constraints,
                    frame_state=frame_state,
                    distributed_state=distributed_state,
                    package=package,
                )
        except exc.SkipFrame as e:
            if one_graph:
                log.debug("No graph captured with export/fullgraph=True")
            assert e._torch_dynamo_tracer_output is not None
            return ConvertFrameReturn(), e._torch_dynamo_tracer_output

        assert distributed_state is None or distributed_state.all_states is not None, (  # type: ignore[has-type]
            "compiler collective wasn't run before compilation completed"
        )
        out_code = dynamo_output.bytecode
        tracer_output = dynamo_output.tracer_output
        if dynamo_output.last_attempt_start_time is not None:
            last_attempt_start_time = dynamo_output.last_attempt_start_time

        assert out_code is not None
        log_bytecode(
            "MODIFIED BYTECODE",
            code.co_name,
            code.co_filename,
            code.co_firstlineno,
            out_code,
        )
        # Dump the MODIFIED bytecode of resumption frame into TORCH_TRACE
        # log file, so that it is parsed by tlparse tool.
        if is_resumption_frame:
            torch._logging.trace_structured(
                "artifact",
                metadata_fn=lambda: {
                    "name": code.co_name + "_MODIFIED_BYTECODE",
                    "encoding": "string",
                },
                payload_fn=lambda: dis.Bytecode(out_code).dis(),
            )

        assert tracer_output.output_graph is not None
        output = tracer_output.output_graph
        code_context.get_context(out_code)[_BYTECODE_HOOK_SIDE_EFFECTS_CONTEXT_KEY] = (
            tuple(output.get_replayed_side_effect_source_refs())
        )

        for idx, hook in enumerate(_bytecode_hooks.values()):
            with dynamo_timed(f"bytecode_hooks_{idx}", log_pt2_compile_event=True):
                hook_output = hook(code, out_code)
                if hook_output is not None:
                    if hook_output is not out_code:
                        _copy_code_context(out_code, hook_output)
                    out_code = hook_output

        orig_code_map[out_code] = code
        output_codes.add(out_code)
        dynamo_time_before_restart = last_attempt_start_time - start_time

        from .bytecode_debugger import BREAKPOINT_MARKER

        if BREAKPOINT_MARKER in out_code.co_consts:
            from torch._C._dynamo.eval_frame import register_breakpoint_code

            register_breakpoint_code(out_code)

        # Tests for new code objects.
        # The rationale for these tests can be found in torch/csrc/dynamo/eval_frame.c
        # Only test once the code object is created.
        # They are not tested during runtime.

        def count_args(code: CodeType) -> int:
            import inspect

            return (
                code.co_argcount
                + code.co_kwonlyargcount
                + bool(code.co_flags & inspect.CO_VARARGS)
                + bool(code.co_flags & inspect.CO_VARKEYWORDS)
            )

        assert out_code is not None

        total_argcount_old = count_args(code)
        total_argcount_new = count_args(out_code)
        msg = "arg mismatch: "
        msg += f"old code object has args {code.co_varnames[:total_argcount_old]}, "
        msg += f"new code object has args {out_code.co_varnames[:total_argcount_new]}"
        assert (
            code.co_varnames[:total_argcount_old]
            == out_code.co_varnames[:total_argcount_new]
        ), msg

        msg = "free var mismatch: "
        msg += f"old code object has free var {code.co_freevars}, "
        msg += f"new code object has free var {out_code.co_freevars}"
        assert code.co_freevars == out_code.co_freevars, msg

        msg = "cell var mismatch: "
        msg += f"old code object has cell var {code.co_cellvars}, "
        msg += f"new code object has cell var {out_code.co_cellvars}"
        assert code.co_cellvars == out_code.co_cellvars, msg

        # Skipping Dynamo on a frame without any extracted graph.
        # This does not affect eager functionality. But this is necessary
        # for export for cases where Dynamo-reconstructed bytecode can create
        # new function frames, confusing export in thinking that there
        # are extra graphs now.

        if output.export and output.is_empty_graph():
            return ConvertFrameReturn(), tracer_output

        assert output.guards is not None
        CleanupManager.instance[out_code] = output.cleanups
        nonlocal cache_entry
        # Temporarily restore the mode stack so guard expressions that
        # reference modes can evaluate.  DisableTorchFunction prevents
        # __torch_function__ dispatch during guard construction so modes
        # with mutable state aren't triggered.
        build_guards_ctx = contextlib.ExitStack()
        if torch_function_mode_stack_state_mgr.stack:
            build_guards_ctx.enter_context(
                torch_function_mode_stack_state_mgr.temp_restore_stack()
            )
        with dynamo_timed("build_guards", log_pt2_compile_event=True), build_guards_ctx:
            check_fn = dynamo_output.build_guards(
                code,
                hooks=hooks,
                save=package is not None,
                cache_entry=cache_entry,
            )

        if package is not None:
            assert check_fn.guards_state is not None
            package.add_guarded_code(check_fn.guards_state, out_code)
            package.add_inlined_source(output.tracing_context.traced_code)
            package.update_device_type(output.current_tracer.graph)

        compile_id_str = str(compile_id) if compile_id is not None else "Unknown"
        annotation_str = "Torch-Compiled Region: " + compile_id_str
        guarded_code = GuardedCode(
            out_code,
            check_fn.guard_manager,  # type: ignore[arg-type]
            compile_id,
            annotation_str,
        )

        if not output.is_empty_graph() and hooks.guard_export_fn is not None:
            # We should not run the guard_export_fn when Dynamo does not
            # generate any graph. This can happen in export when TorchDynamo
            # generated bytecode has some reconstruction logic for mutated
            # variables which can trigger TorchDynamo on the children frames but
            # they are benign and do not generate any new graphs.
            hooks.guard_export_fn(output.guards)

        return wrap_guarded_code(guarded_code), tracer_output

    metrics_context = get_metrics_context()
    package_code_context = (
        package.code_context(code) if package is not None else contextlib.nullcontext()
    )
    with (
        _use_lazy_graph_module(config.use_lazy_graph_module),
        compile_context(CompileContext(compile_id)),
        chromium_event_timed(
            "dynamo", reset_event_log_on_exit=True, log_pt2_compile_event=True
        ),
        _WaitCounter("pytorch.wait_counter.entire_forward_compile").guard(),
        metrics_context,
        dynamo_timed(
            "_compile.compile_inner",
            phase_name="entire_frame_compile",
            dynamo_compile_column_us="dynamo_cumulative_compile_time_us",
        ),
        package_code_context,
    ):
        restart_reasons: set[str] = set()
        if compile_pg := get_compile_pg():
            distributed_state = DistributedState(compile_pg, LocalState())
        else:
            distributed_state = None

        # Check recompilations
        recompile_reason: str | None = None
        if is_recompilation(cache_size) and frame:
            reasons = get_and_maybe_log_recompilation_reasons(
                cache_entry, frame, innermost_fn(compiler_fn)
            )
            recompile_reason = (
                "Unable to find recompilation reasons" if not reasons else reasons[0]
            )
        metrics_context.update_outer(
            {
                "recompile_reason": recompile_reason,
                "inline_inbuilt_nn_modules_candidate": False,
            }
        )

        recompile_user_contexts = get_hook_for_recompile_user_context()
        if recompile_user_contexts:
            # cap each user context to N chars for data retention purposes. N=256
            # is chosen to be large enough to capture the most important info.
            user_contexts_msg = {
                user_context()[:256] for user_context in recompile_user_contexts
            }
            metrics_context.set("recompile_user_contexts", user_contexts_msg)

        exceeded, limit_type = exceeds_recompile_limit(cache_size, compile_id)
        if exceeded:

            def format_func_info(code: CodeType) -> str:
                return f"'{code.co_name}' ({code.co_filename}:{code.co_firstlineno})"

            # NS: Don't add period at the end of string, as it'll be added to URL
            # rendering it incorrect
            log.warning(
                "torch._dynamo hit config.%s (%s)\n"
                "   function: %s\n"
                "   last reason: %s\n"
                'To log all recompilation reasons, use TORCH_LOGS="recompiles".\n'
                "To diagnose recompilation issues, see %s",
                limit_type,
                getattr(config, limit_type),
                format_func_info(code),
                recompile_reason,
                troubleshooting_url,
            )

            def raise_unimplemented_cache_limit_exceeded() -> NoReturn:
                unimplemented(
                    gb_type="Dynamo recompile limit exceeded",
                    context=f"Limit type: {limit_type}",
                    explanation="Dynamo attempted to recompile the code object too many times, "
                    f"exceeding the {limit_type} cache size limit (currently set to {getattr(config, limit_type)}). "
                    "Excessive recompilations can degrade "
                    "performance due to the compilation overhead of each recompilation.",
                    hints=[
                        "To monitor recompilations, enable TORCH_LOGS=recompiles. "
                        "If recompilations are expected, consider "
                        f"increasing torch._dynamo.config.{limit_type} to an appropriate value.",
                        f"See {troubleshooting_url} for tips on dealing with recompilations.",
                    ],
                )

            try:
                raise_unimplemented_cache_limit_exceeded()
            except Unsupported as e:
                if config.fail_on_recompile_limit_hit:
                    raise FailOnRecompileLimitHit(
                        "Hard failure due to fail_on_recompile_limit_hit"
                    ) from e
                elif one_graph:
                    raise FailOnRecompileLimitHit(
                        "Hard failure due to fullgraph=True"
                    ) from e
                else:
                    # Set frame execution strategy to RUN_ONLY for this recompile limit case
                    e.frame_exec_strategy = FrameExecStrategy(
                        FrameAction.RUN_ONLY, FrameAction.RUN_ONLY
                    )
                    raise

        log.debug(
            "torchdynamo start compiling %s %s:%s, stack (elided %s frames):\n%s",
            code.co_name,
            code.co_filename,
            code.co_firstlineno,
            skip + 2,
            # -2: omit current frame, omit contextlib decorator
            "".join(CapturedTraceback.extract(skip=2 + skip).format()),
        )
        # -4: -2 as above, plus trace_structured frames
        #
        # NB: the frame looks like this:
        #
        # # handled by skip argument
        # torch/_dynamo/convert_frame.py:1069 in catch_errors
        # torch/_dynamo/convert_frame.py:910 in _convert_frame
        # torch/_dynamo/convert_frame.py:464 in _convert_frame_assert
        # torch/_utils_internal.py:70 in wrapper_function
        #
        # # 2 current frame and context lib
        # env/lib/python3.10/contextlib.py:79 in inner
        # torch/_dynamo/convert_frame.py:776 in _compile
        #
        # # 2 extra here
        # torch/_logging/_internal.py:1064 in trace_structured
        # torch/_dynamo/convert_frame.py:780 in <lambda>
        stack_trace = log_dynamo_start(code, skip)
        start_time_ns = time.time_ns()
        fail_type: str | None = None
        fail_reason: str | None = None
        exception_stack_trace: list[str] | None = None
        fail_user_frame_filename: str | None = None
        fail_user_frame_lineno: int | None = None
        torch._dynamo.utils.ReinplaceCounters.clear()
        guarded_code = None
        tracer_output = None

        if (
            config.debug_backend_override
            or config.debug_dynamo_config_override
            or config.debug_inductor_config_override
        ):
            # Eagerly validate config override strings before entering the
            # compilation try/except so that typos surface as clean ValueErrors
            # instead of being wrapped as InternalTorchDynamoError.
            from .graph_id_filter import (
                _validate_backend_names,
                _validate_dynamo_config_keys,
                _validate_inductor_config_keys,
            )

            if err := _validate_backend_names(config.debug_backend_override):
                raise ValueError(err)
            if err := _validate_dynamo_config_keys(config.debug_dynamo_config_override):
                raise ValueError(err)
            if err := _validate_inductor_config_keys(
                config.debug_inductor_config_override
            ):
                raise ValueError(err)

        try:
            guarded_code, tracer_output = compile_inner(code, one_graph, hooks)

            # NB: We only put_code_state in success case.  Success case here
            # does include graph breaks; specifically, if a graph break still
            # resulted in a partially compiled graph, we WILL return here.  An
            # Unsupported exception will only bubble to the top level if we
            # are unable to compile the frame at all.  In this case, there's
            # no point in uploading the code state, because we will always
            # fail exactly the same way even without the update.  (It's useful
            # to upload for graph break though, because this can prevent
            # extra graph break compilations.)
            put_code_state()
            if (
                tracer_output
                and (output_graph := tracer_output.output_graph)
                and output_graph.has_outputs()
            ):
                log_frame_dynamic_whitelist(code)
                if recompile_reason and "size mismatch at index" in recompile_reason:
                    _log_size_mismatch_recompile()

            clear_compile_context_weakrefs(tracer_output, compiler_fn)
            return guarded_code
        except Exception as e:
            # NB: e's msg is mutated here to add user stack, but we DON'T want
            # that stack in the Scuba logged fail_reason. So we grab the fail
            # info here and add it to the metrics context below.
            fail_type = type(e).__qualname__
            fail_reason = str(e)
            exception_stack_trace = [traceback.format_exc()]
            exception_handler(e, code, frame, export=export)
            # NB: this is the post-mutation exception
            torch._logging.trace_structured(
                "artifact",
                metadata_fn=lambda: {
                    "name": "dynamo_error",
                    "encoding": "string",
                },
                payload_fn=lambda: traceback.format_exc(),
            )
            fail_user_frame_filename, fail_user_frame_lineno = exc.get_exc_message(
                e, compile_id
            )
            tracer_output = getattr(e, "_torch_dynamo_tracer_output", None)
            if isinstance(
                e,
                (
                    Unsupported,
                    UserError,
                    TorchRuntimeError,
                    BackendCompilerFailed,
                    AssertionError,
                    ConstraintViolationError,
                    GuardOnDataDependentSymNode,
                    ValidationException,
                    UncapturedHigherOrderOpError,
                    BisectValidationException,
                    ShortenTraceback,
                    PackageError,
                    ResumePrologueTracingError,
                ),
            ):
                raise
            else:
                # Rewrap for clarity
                raise InternalTorchDynamoError(
                    f"{type(e).__qualname__}: {str(e)}"
                ).with_traceback(e.__traceback__) from None
        finally:
            # === WARNING WARNING WARNING ===
            # If you commit a bug here, it will suppress writing to
            # dynamo_compile table, and we will not have telemetry.
            # Be extra careful when making changes here!

            if torch._dynamo.config.run_gc_after_compile:
                with dynamo_timed("gc", dynamo_compile_column_us="gc_time_us"):
                    log.info("run_gc_after_compile: running gc")
                    gc.collect(1)

            output = None
            if tracer_output:
                output = tracer_output.output_graph
            if output:
                # pyrefly: ignore [implicit-any]
                output.local_scope = {}
                # tracer should already be None, keep an extra check here just in case.
                if tracer := output.root_tx:
                    # pyrefly: ignore [implicit-any]
                    tracer.f_locals = {}

            from .utils import curr_frame

            frame_key = str(curr_frame)
            if fail_reason is None and output is not None:
                guard_count = len(output.guards)
                shape_env_guard_count = len(output.shape_env.guards)
                graph_op_count = output.count_calls()
                graph_node_count = len(output.graph.nodes)
                graph_node_shapes = output.get_graph_sizes_structured()
                graph_input_count = len(output.placeholders)
                non_compliant_ops = {op.__qualname__ for op in output.non_compliant_ops}
                compliant_custom_ops = {
                    op.__qualname__ for op in output.compliant_custom_ops
                }
                torch._dynamo.utils.ReinplaceCounters.log()
            else:
                guard_count = None
                shape_env_guard_count = None
                graph_op_count = None
                graph_node_count = None
                # pyrefly: ignore [implicit-any]
                graph_node_shapes = {}
                graph_input_count = None
                non_compliant_ops = set({})
                compliant_custom_ops = set({})
                restart_reasons = set()
                # If compilation failed, the entire time is wasted
                dynamo_time_before_restart = (time.time_ns() - start_time_ns) / 1e9

            metrics = {
                "frame_key": frame_key,
                "co_name": code.co_name,
                "co_filename": code.co_filename,
                "co_firstlineno": code.co_firstlineno,
                "cache_size": cache_size.num_cache_entries_with_same_id_matched_objs,
                "accumulated_cache_size": cache_size.num_cache_entries,
                "guard_count": guard_count,
                "shape_env_guard_count": shape_env_guard_count,
                "graph_op_count": graph_op_count,
                "graph_node_count": graph_node_count,
                "graph_input_count": graph_input_count,
                "fail_type": fail_type,
                "fail_reason": fail_reason,
                "fail_user_frame_filename": fail_user_frame_filename,
                "fail_user_frame_lineno": fail_user_frame_lineno,
                "non_compliant_ops": non_compliant_ops,
                "compliant_custom_ops": compliant_custom_ops,
                "restart_reasons": restart_reasons,
                "dynamo_time_before_restart_s": dynamo_time_before_restart,
                "has_guarded_code": guarded_code is not None,
                "specialize_float": config.specialize_float,
                "is_forward": True,
                "dynamo_compile_time_before_restart_us": to_int_us(
                    dynamo_time_before_restart
                ),
                "stack_trace": stack_trace,
                "graph_node_shapes": str(graph_node_shapes),
                "exception_stack_trace": exception_stack_trace,
            }
            # TODO: replace with CompileEventLogger.compilation_metrics
            # There are some columns here not in PT2 Compile Events
            # so we need to slightly change it
            metrics_context.update_outer(metrics)
            # === END WARNING WARNING WARNING ===

            # If tracer is available, then tracer.error_on_graph_break reflects value of
            # global symbolic_convert.error_on_graph_break at the time of the graph break -
            # symbolic_convert.error_on_graph_break may have been (correctly) changed during cleanup.
            # If tracer is unavailable, then fallback to symbolic_convert.error_on_graph_break.
            if convert_frame_box:
                convert_frame_box.error_on_graph_break = (
                    tracer_output.error_on_graph_break
                    if tracer_output
                    else _get_error_on_graph_break()
                )

            # Cleanup guards unless if in export, which will return guards
            # Make sure to do this after collecting metrics
            if (
                tracer_output is not None
                and tracer_output.output_graph is not None
                and not tracer_output.output_graph.export
            ):
                tracer_output.output_graph.tracing_context.guards_context.dynamo_guards.clear()

            clear_compile_context_weakrefs(tracer_output, compiler_fn)