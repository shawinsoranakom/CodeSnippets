def _create_runtime_wrapper(
    compiled_fn: Callable[..., Any],
    *,
    runtime_metadata: ViewAndMutationMeta,
    indices_of_inps_to_detach: list[int],
    trace_joint: bool,
    keep_input_mutations: bool,
    disable_amp: bool,
) -> Callable[..., Any]:
    compiled_invoker = _RuntimeCompiledFnInvoker(
        compiled_fn=compiled_fn,
        indices_of_inps_to_detach=indices_of_inps_to_detach,
        trace_joint=trace_joint,
        disable_amp=disable_amp,
    )
    runtime_epilogue = _RuntimeForwardEpilogue(
        runtime_metadata=runtime_metadata,
        trace_joint=trace_joint,
        keep_input_mutations=keep_input_mutations,
    )

    # Codegen output alias regeneration: emit straight-line code per output
    # with all handler branches resolved at compile time.
    if runtime_metadata.num_outputs_aliased > 0:
        output_handlers = runtime_epilogue.output_handlers
        alias_lines = ["def _alias_fn(orig_inputs, fw_outs):"]
        alias_lines.append("    ret_outs = []")
        alias_globals: dict[str, object] = {
            "gen_alias_from_base": gen_alias_from_base,
            "_unwrap_tensoralias": _unwrap_tensoralias,
        }
        for i, handler in enumerate(output_handlers):
            if isinstance(handler, NoopAliasHandler):
                alias_lines.append(f"    ret_outs.append(fw_outs[{i}])")
            elif isinstance(handler, IsInputHandler):
                alias_lines.append(
                    f"    ret_outs.append(orig_inputs[{handler.base_idx}])"
                )
            elif isinstance(handler, AliasOfInputHandler):
                vms_name = f"_vms_{i}"
                alias_globals[vms_name] = handler.view_meta_sequence
                out_expr = (
                    f"_unwrap_tensoralias(fw_outs[{i}])"
                    if trace_joint
                    else f"fw_outs[{i}]"
                )
                alias_lines.append(
                    f"    ret_outs.append(gen_alias_from_base("
                    f"orig_inputs[{handler.base_idx}], {out_expr}, "
                    f"{handler.requires_grad!r}, {vms_name}, "
                    f"replay_views={handler.replay_views!r}))"
                )
            elif isinstance(handler, AliasOfIntermediateHandler):
                vms_name = f"_vms_{i}"
                alias_globals[vms_name] = handler.view_meta_sequence
                out_expr = (
                    f"_unwrap_tensoralias(fw_outs[{i}])"
                    if trace_joint
                    else f"fw_outs[{i}]"
                )
                base_unwrap = handler._unwrap_aliased_base_tensor is _unwrap_tensoralias
                base_expr = (
                    f"_unwrap_tensoralias(fw_outs[{handler.base_idx}])"
                    if base_unwrap
                    else f"fw_outs[{handler.base_idx}]"
                )
                alias_lines.append(
                    f"    ret_outs.append(gen_alias_from_base("
                    f"{base_expr}, {out_expr}, "
                    f"{handler.requires_grad!r}, {vms_name}, "
                    f"replay_views={handler.replay_views!r}))"
                )
            else:
                raise AssertionError(
                    f"unhandled output handler type: {type(handler).__name__}"
                )
        alias_lines.append("    return ret_outs")
        alias_source = "\n".join(alias_lines)

        from .subclass_codegen import _compile_and_exec_source

        _codegen_alias_fn = _compile_and_exec_source(
            alias_source, alias_globals, "_alias_fn", "output_alias_wrapper"
        )
        import types

        def _replay_alias(self, orig_inputs, fw_outs):
            return _codegen_alias_fn(orig_inputs, fw_outs)

        runtime_epilogue._replay_output_aliases = types.MethodType(  # type: ignore[attr-defined]
            _replay_alias,
            runtime_epilogue,
        )

    def record_runtime_wrapper_prologue_enter() -> AbstractContextManager[None] | None:
        if (
            torch.autograd.profiler._is_profiler_enabled
            and dynamo_config.record_runtime_overhead
        ):
            cm = torch._C._profiler._RecordFunctionFast(
                "AOTDispatcher Runtime Wrapper Prologue"
            )
            cm.__enter__()
            return cm
        return None

    def record_runtime_wrapper_prologue_exit(
        cm: AbstractContextManager[None] | None,
    ) -> None:
        if cm is not None:
            cm.__exit__(None, None, None)

    # Codegen mutation epilogue: emit straight-line code per mutated input
    # with all branches resolved at compile time.
    if runtime_metadata.num_mutated_inp_runtime_indices > 0:
        mut_lines = ["def _apply_mutations(orig_inputs, updated_inputs):"]
        mut_globals: dict[str, object] = {
            "torch": torch,
            "_unwrap_tensoralias": _unwrap_tensoralias,
        }
        for i, inpt_idx in enumerate(runtime_metadata.mutated_inp_runtime_indices):
            meta = runtime_metadata.input_info[inpt_idx]
            if not meta.mutates_data and not meta.mutates_metadata:
                continue
            oi = f"orig_inputs[{inpt_idx}]"
            ui = f"updated_inputs[{i}]"
            if meta.mutates_storage_metadata:
                if trace_joint:
                    mut_lines.append(f"    _u{i} = _unwrap_tensoralias({ui})")
                else:
                    mut_lines.append(f"    _u{i} = {ui}")
                mut_lines.append(f"    with torch.no_grad(): {oi}.set_(_u{i})")
            elif meta.mutates_metadata and not meta.mutates_data:
                if trace_joint:
                    mut_lines.append(f"    _u{i} = _unwrap_tensoralias({ui})")
                else:
                    mut_lines.append(f"    _u{i} = {ui}")
                mut_lines.append(
                    f"    {oi}.as_strided_(_u{i}.size(), _u{i}.stride(), _u{i}.storage_offset())"
                )
            else:
                if meta.mutates_data and meta.mutates_metadata:
                    mut_lines.append(
                        f"    {oi}.as_strided_({ui}.size(), {ui}.stride(), {ui}.storage_offset())"
                    )
                else:
                    assert meta.mutates_data, (  # noqa: S101
                        f"expected mutates_data for input {inpt_idx}"
                    )
                if meta.is_leaf:
                    mut_lines.append(
                        f"    if {oi}.requires_grad: {oi}.detach().copy_({ui})"
                    )
                    mut_lines.append(f"    else: {oi}.copy_({ui})")
                else:
                    has_stream = (
                        runtime_metadata.mutated_inp_stream_indices is not None
                        and i < len(runtime_metadata.mutated_inp_stream_indices)
                        and runtime_metadata.mutated_inp_stream_indices[i] is not None
                    )
                    if has_stream:
                        msg_name = f"_stream_err_{i}"
                        mut_globals[msg_name] = (
                            "Mutations on inputs with user-specified streams are not yet supported. "
                            "See: https://github.com/pytorch/pytorch/issues/172522"
                        )
                        mut_lines.append(f"    raise RuntimeError({msg_name})")
                    else:
                        mut_lines.append(f"    {oi}.copy_({ui})")
        if len(mut_lines) == 1:
            mut_lines.append("    pass")
        mut_source = "\n".join(mut_lines)

        from .subclass_codegen import _compile_and_exec_source

        codegen_apply_mutations = _compile_and_exec_source(
            mut_source, mut_globals, "_apply_mutations", "mutation_epilogue"
        )
        import types

        runtime_epilogue._apply_input_mutations = types.MethodType(  # type: ignore[attr-defined]
            lambda self, orig_inputs, updated_inputs: codegen_apply_mutations(
                orig_inputs, updated_inputs
            ),
            runtime_epilogue,
        )

    @simple_wraps(compiled_invoker.compiled_fn)
    def runtime_wrapper(args: list[Any]) -> Any:
        # Create context manager for profiler
        cm = record_runtime_wrapper_prologue_enter()
        prologue_exited = False

        def exit_prologue() -> None:
            nonlocal prologue_exited
            if not prologue_exited:
                record_runtime_wrapper_prologue_exit(cm)
                prologue_exited = True

        try:
            # stash a ref to each input tensor we plan to use after the compiled function
            orig_inputs = runtime_epilogue.capture_orig_inputs(args)
            runtime_epilogue.increment_mutation_versions(args)
            all_outs = compiled_invoker.run(args, on_before_call=exit_prologue)
        finally:
            exit_prologue()

        del args
        return runtime_epilogue.finalize(orig_inputs, all_outs)

    if not (trace_joint and _should_disable_saved_tensors_hooks()):
        return runtime_wrapper

    # Disabling saved tensors hooks
    @simple_wraps(runtime_wrapper)
    def _runtime_wrapper(*args: Any, **kwargs: Any) -> Any:
        with _disable_saved_tensors_hooks():
            return runtime_wrapper(*args, **kwargs)

    return _runtime_wrapper