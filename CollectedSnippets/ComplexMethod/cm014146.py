def _make_handler(
        fn: Callable[..., Any], arg_types: list[type], has_kwargs: bool
    ) -> Callable[
        [
            "InstructionTranslator",
            list[VariableTracker],
            dict[str, VariableTracker],
        ],
        VariableTracker | None,
    ]:
        from .lazy import LazyVariableTracker

        obj = BuiltinVariable(fn)
        handlers: list[_HandlerCallback] = []

        if any(issubclass(t, LazyVariableTracker) for t in arg_types):
            return lambda tx, args, kwargs: obj.call_function(
                tx, [v.realize() for v in args], kwargs
            )

        if inspect.isclass(fn) and (
            issubclass(fn, BaseException)
            # GeneratorExit doesn't inherit from Exception
            # >>> issubclass(GeneratorExit, Exception)
            # False
            or fn is GeneratorExit
        ):

            def create_exception_class_object(
                tx: "InstructionTranslator",
                args: list[VariableTracker],
                kwargs: dict[str, VariableTracker],
            ) -> VariableTracker:
                if fn is AssertionError and not all(
                    x.is_python_constant() and isinstance(x.as_python_constant(), str)
                    for x in args
                ):
                    unimplemented(
                        gb_type="assert with non-string message",
                        context=str(args),
                        explanation="Dynamo only supports asserts with string messages",
                        hints=[*graph_break_hints.SUPPORTABLE],
                    )

                return variables.ExceptionVariable(fn, args, kwargs)

            return create_exception_class_object

        if obj.can_insert_in_graph() and not (
            fn is operator.getitem
            and not issubclass(arg_types[0], variables.TensorVariable)
        ):
            if obj.tensor_args_type(arg_types):
                return obj._handle_insert_op_in_graph
            elif has_kwargs:
                # need runtime check for kwargs
                handlers.append(obj._handle_insert_op_in_graph)

        # Handle binary ops (e.g. __add__ / __radd__, __iadd__, etc.)
        # NB: Tensor args are handled above and not here
        if len(arg_types) == 2 and not has_kwargs:
            # Try to find a handler for the arg types; otherwise, fall through to constant handler
            binop_handlers = BuiltinVariable._find_binop_handler(fn, *arg_types)
            if not binop_handlers:
                pass
            elif len(binop_handlers) == 1:
                (binop_handler,) = binop_handlers
                handlers.append(lambda tx, args, _: binop_handler(tx, *args))
            else:

                def call_binop_handlers(
                    tx: "InstructionTranslator", args: Any, _: Any
                ) -> Any:
                    # pyrefly: ignore [not-iterable]
                    for fn in binop_handlers:
                        rv = fn(tx, *args)
                        if rv:
                            return rv
                    return None

                handlers.append(call_binop_handlers)

        self_handler = getattr(obj, f"call_{fn.__name__}", None)
        if self_handler:

            def call_self_handler(
                tx: "InstructionTranslator",
                args: Sequence[VariableTracker],
                kwargs: dict[str, VariableTracker],
            ) -> VariableTracker | None:
                try:
                    # pyrefly: ignore [not-callable]
                    return self_handler(tx, *args, **kwargs)
                except TypeError:
                    # Check if binding is bad. inspect signature bind is expensive.
                    # So check only when handler call fails.
                    try:
                        # pyrefly: ignore [bad-argument-type]
                        inspect.signature(self_handler).bind(tx, *args, **kwargs)
                    except TypeError as e:
                        has_constant_handler = obj.has_constant_handler(args, kwargs)
                        if not has_constant_handler:
                            log.warning(
                                "incorrect arg count %s %s and no constant handler",
                                self_handler,
                                e,
                            )
                            unimplemented(
                                gb_type="invalid call to builtin op handler",
                                context=f"invalid args to {self_handler}: {args} {kwargs}",
                                explanation=f"Encountered TypeError when trying to handle op {fn.__name__}",
                                hints=[*graph_break_hints.DIFFICULT],
                            )
                    else:
                        raise
                except Unsupported as exc:
                    has_constant_handler = obj.has_constant_handler(args, kwargs)
                    if not has_constant_handler:
                        raise
                    # Actually, we will handle this just fine
                    exc.remove_from_stats()
                return None

            handlers.append(call_self_handler)

        if obj.can_constant_fold_through():
            if (
                all(issubclass(x, ConstantVariable) for x in arg_types)
                and not has_kwargs
            ):

                def constant_fold_handler(
                    tx: "InstructionTranslator",
                    args: Sequence[VariableTracker],
                    kwargs: dict[str, VariableTracker],
                ) -> VariableTracker | None:
                    # fast path
                    try:
                        res = fn(
                            *[x.as_python_constant() for x in args],
                        )
                    except Exception as exc:
                        raise_observed_exception(
                            type(exc),
                            tx,
                            args=list(exc.args),
                        )
                    except AsPythonConstantNotImplementedError as exc:
                        unimplemented(
                            gb_type="constant fold exception",
                            context=f"attempted to run function {fn} with arguments {args}",
                            explanation="Encountered exception when attempting to constant fold.",
                            hints=[*graph_break_hints.DYNAMO_BUG],
                            from_exc=exc,
                        )
                    return VariableTracker.build(tx, res)

            else:

                def constant_fold_handler(
                    tx: "InstructionTranslator",
                    args: Sequence[VariableTracker],
                    kwargs: dict[str, VariableTracker],
                ) -> VariableTracker | None:
                    # path with a runtime check
                    if check_unspec_or_constant_args(args, kwargs):
                        try:
                            res = fn(
                                *[x.as_python_constant() for x in args],
                                **{
                                    k: v.as_python_constant() for k, v in kwargs.items()
                                },
                            )
                        except AsPythonConstantNotImplementedError as exc:
                            unimplemented(
                                gb_type="constant fold exception",
                                context=f"attempted to run function {fn} with arguments {args}",
                                explanation="Encountered exception when attempting to constant fold.",
                                hints=[*graph_break_hints.DYNAMO_BUG],
                                from_exc=exc,
                            )
                        except Exception as exc:
                            raise_observed_exception(
                                type(exc),
                                tx,
                                args=list(exc.args),
                            )
                        return VariableTracker.build(tx, res)
                    return None

            handlers.append(constant_fold_handler)

        def call_unimplemented(args: Sequence[VariableTracker]) -> None:
            real_arg_types = [arg.python_type_name() for arg in args]
            unimplemented(
                gb_type="Failed to trace builtin operator",
                context=f"builtin {fn.__name__} {arg_types} {has_kwargs}",
                explanation=f"Dynamo does not know how to trace builtin operator `{fn.__name__}` "
                f"with argument types {real_arg_types} (has_kwargs {has_kwargs})",
                hints=[
                    f"Avoid calling builtin `{fn.__name__}` with argument types {real_arg_types}. "
                    f"Consider using an equivalent alternative function/method to `{fn.__name__}`.",
                    "If you are attempting to call a logging function (e.g. `print`), "
                    "you can try adding it to `torch._dynamo.config.reorderable_logging_functions`.",
                    "Please report an issue to PyTorch.",
                ],
            )

        if len(handlers) == 0:
            return lambda tx, args, kwargs: call_unimplemented(args)
        elif len(handlers) == 1:
            (handler,) = handlers

            def builtin_dispatch(
                tx: "InstructionTranslator",
                args: Sequence[VariableTracker],
                kwargs: dict[str, VariableTracker],
            ) -> VariableTracker | None:
                rv = handler(tx, args, kwargs)
                if rv:
                    return rv
                call_unimplemented(args)
                return rv

        else:

            def builtin_dispatch(
                tx: "InstructionTranslator",
                args: Sequence[VariableTracker],
                kwargs: dict[str, VariableTracker],
            ) -> VariableTracker | None:
                rv = None
                for fn in handlers:
                    rv = fn(tx, args, kwargs)
                    if rv:
                        return rv
                call_unimplemented(args)
                return rv

        return builtin_dispatch