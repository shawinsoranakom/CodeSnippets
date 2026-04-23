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