def build_inline_tracer(
        parent: Any,
        func: BaseUserFunctionVariable,
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> InliningInstructionTranslator:
        assert isinstance(
            func,
            (
                UserFunctionVariable,
                NestedUserFunctionVariable,
                LocalGeneratorFunctionVariable,
            ),
        )
        code: types.CodeType = func.get_code()
        result = None
        tracing_ctx = parent.output.tracing_context

        # Check if we have already identified this function to be inline-able.
        # The exception is dont_skip_tracing flag which affects the inline
        # behavior. If the flag is True, don't rely on previous results.
        if not config.dont_skip_tracing and tracing_ctx:
            if previous_result := tracing_ctx.previously_inlined_functions.get(
                code, None
            ):
                result = previous_result

        if result is None:
            result = InliningInstructionTranslator.check_inlineable(func)
            assert result.skipped is False

            if not config.dont_skip_tracing and tracing_ctx:
                tracing_ctx.previously_inlined_functions[code] = result

        sub_locals = None
        try:
            sub_locals = func.bind_args(parent, args, kwargs)
        except TypeError as e:
            unimplemented(
                gb_type="failed to bind arguments when attempting to inline",
                context=f"func='{func.get_name()}' {func.get_filename()}:{func.get_code().co_firstlineno}; "
                f"args = {[arg.python_type() for arg in args]}; kwargs = {kwargs}",
                explanation=f"Argument mismatch when attempting to trace function {func.get_name()}.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
                from_exc=e,
            )

        assert sub_locals is not None

        for v in itertools.chain(sub_locals.values()):
            if not isinstance(v, VariableTracker):
                unimplemented(
                    gb_type="Encountered unconverted argument when attempting to inline",
                    context=f"func: {func}, arg: {v}",
                    explanation="An argument to an inlined function was not successfully converted to a VariableTracker.",
                    hints=[*graph_break_hints.DYNAMO_BUG],
                )

        if code.co_name in ("__setitem__", "__setattr__") and not (
            args and isinstance(args[0], variables.UserDefinedObjectVariable)
        ):
            unimplemented(
                gb_type="Unsupported __setitem__/__setattr__ inline attempt",
                context=f"code name: {code.co_name}, args: {args}",
                explanation=f"Attempted to inline {code.co_name} where first argument (self) is not a user-defined object.",
                hints=[],
            )

        suffix = ""
        # TODO: mlazos, add support for enabling multiple artifact logs
        # with a single alias
        if torch._logging._internal.log_state.is_artifact_enabled("bytecode"):
            suffix = f"\n{dis.Bytecode(code).dis()}"
        if sys.version_info >= (3, 11):
            cur_inst = parent.current_instruction
            parent_code = parent.f_code

            def get_trace_call_log_str() -> str:
                header = parent.get_line_of_code_header(
                    lineno=cur_inst.positions.lineno
                )
                line = get_instruction_source_311(parent_code, cur_inst).rstrip()
                return f"TRACE inlined call {code.co_name} from {header}\n{line}"

            trace_call_log.debug("%s", LazyString(get_trace_call_log_str))
        log.debug("INLINING %s%s, %s", code, suffix, result.reason)

        # Detect inline GraphModule calls in order to propagate node metadata,
        # by checking if the first argument (self) is a variable tracking a GraphModule.
        # For unrealized lazy VTs, use peek_type to skip non-Module args
        # without realizing them (which would install unnecessary guards).
        if args:
            arg0 = args[0]
            should_check = True
            if isinstance(arg0, LazyVariableTracker) and not arg0.is_realized():
                if issubclass(arg0.peek_type(), torch.nn.Module):
                    arg0 = arg0.realize()
                else:
                    should_check = False

            if should_check:
                if isinstance(arg0, NNModuleVariable):
                    module = parent.output.get_submodule(arg0.module_key)
                    if isinstance(module, torch.fx.GraphModule):
                        code_context.get_context(module.forward.__code__)[
                            "orig_graphmodule"
                        ] = weakref.ref(module)
                elif isinstance(arg0, UnspecializedNNModuleVariable):
                    module = arg0.value
                    if isinstance(module, torch.fx.GraphModule):
                        code_context.get_context(module.forward.__code__)[
                            "orig_graphmodule"
                        ] = weakref.ref(module)

        assert not isinstance(func, SkipFunctionVariable)
        tracer: InliningInstructionTranslator
        if is_generator(code):
            tracer = InliningGeneratorInstructionTranslator(
                parent,
                code,
                sub_locals,
                parent.symbolic_globals,
                parent.symbolic_torch_function_state,
                parent.symbolic_stream_state,
                func,
            )
        else:
            tracer = InliningInstructionTranslator(
                parent,
                code,
                sub_locals,
                parent.symbolic_globals,
                parent.symbolic_torch_function_state,
                parent.symbolic_stream_state,
                func,
            )
        return tracer