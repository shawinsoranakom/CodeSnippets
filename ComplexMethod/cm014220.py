def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from ..side_effects import SideEffects
        from .builder import SourcelessBuilder, wrap_fx_proxy
        from .ctx_manager import GenericContextWrappingVariable

        constant_args = check_constant_args(args, kwargs)

        if torch.distributed.is_available() and self.value is torch.distributed.P2POp:
            if not config.enable_p2p_compilation:
                unimplemented(
                    gb_type="P2P compilation disabled for P2POp construction",
                    context="torch.distributed.P2POp",
                    explanation="P2P compilation is disabled.",
                    hints=[
                        "Set TORCHDYNAMO_ENABLE_P2P_COMPILATION=1 to enable.",
                    ],
                )
            var = tx.output.side_effects.track_new_user_defined_object(
                SourcelessBuilder.create(tx, object),
                self,
                [],
            )
            var.call_method(tx, "__init__", list(args), kwargs)  # type: ignore[arg-type]
            return var

        if self.can_constant_fold_through() and constant_args:
            # constant fold
            return VariableTracker.build(
                tx,
                self.as_python_constant()(  # type: ignore[operator]
                    *[x.as_python_constant() for x in args],
                    **{k: v.as_python_constant() for k, v in kwargs.items()},
                ),
            )
        elif self.value is torch.nn.CrossEntropyLoss:
            return self._call_cross_entropy_loss(tx, args, kwargs)
        elif self.value is contextlib.nullcontext:
            # import here to avoid circular dependency
            from .ctx_manager import NullContextVariable

            return NullContextVariable(*args, **kwargs)
        elif self.value is collections.defaultdict:
            # defaultdict construction — use track_new_user_defined_object
            # which creates DefaultDictVariable. __init__ handler extracts
            # default_factory and populates items.
            from .builder import SourcelessBuilder

            result = tx.output.side_effects.track_new_user_defined_object(
                SourcelessBuilder.create(tx, dict),
                self,
                [],
            )
            result.call_method(tx, "__init__", list(args), kwargs)
            return result
        elif is_typeddict(self.value):
            if self.value.__optional_keys__:  # type: ignore[attr-defined]
                unimplemented(
                    gb_type="TypedDict with optional keys",
                    context=str(self.value),
                    explanation="Dyanmo does not support tracing TypedDict with optional keys",
                    hints=[
                        "Avoid using TypedDict with optional keys",
                        *graph_break_hints.SUPPORTABLE,
                    ],
                )
            return variables.DictBuiltinVariable.call_custom_dict(
                tx, dict, *args, **kwargs
            )
        elif self.value is collections.deque:
            maxlen = variables.ConstantVariable.create(None)

            def deque_signature(
                iterable: Iterable[Any] | None = None, maxlen: int | None = None
            ) -> Any:
                pass

            bound_args = None
            try:
                bound_args = inspect.signature(deque_signature).bind(*args, **kwargs)
            except TypeError as e:
                unimplemented(
                    gb_type="collections.deque() with bad arguments",
                    context=f"args={args}, kwargs={kwargs}",
                    explanation="Detected call to collections.deque() with bad arguments.",
                    hints=[
                        "Fix the call to collections.deque().",
                        *graph_break_hints.USER_ERROR,
                    ],
                    from_exc=e,
                )
            assert bound_args is not None
            if "iterable" in bound_args.arguments:
                if not bound_args.arguments["iterable"].has_force_unpack_var_sequence(
                    tx
                ):
                    unimplemented(
                        gb_type="collections.deque() with bad iterable argument",
                        context=f"args={args}, kwargs={kwargs}",
                        explanation="Call to collections.deque() has an iterable argument that Dynamo cannot "
                        "convert to a list.",
                        hints=[
                            "Use a simpler sequence type that Dynamo can convert to a list "
                            "(e.g. list, tuple, list iterator, etc.)",
                            *graph_break_hints.USER_ERROR,
                        ],
                    )
                items = bound_args.arguments["iterable"].force_unpack_var_sequence(tx)
            else:
                # pyrefly: ignore [implicit-any]
                items = []

            if "maxlen" in bound_args.arguments:
                maxlen = bound_args.arguments["maxlen"]

            return variables.lists.DequeVariable(
                items, maxlen=maxlen, mutation_type=ValueMutationNew()
            )
        elif (
            # https://github.com/python/cpython/blob/33efd7178e269cbd04233856261fd0aabbf35447/Lib/contextlib.py#L475-L477
            self.value is types.MethodType
            and len(args) == 2
            and isinstance(args[0], variables.UserFunctionVariable)
            and isinstance(args[1], GenericContextWrappingVariable)
            and args[0].get_name() in ("__enter__", "__exit__")
        ):
            cm_obj = args[1].cm_obj
            fn = getattr(cm_obj, args[0].get_name()).__func__
            return variables.UserMethodVariable(fn, args[1], source=self.source)
        elif self.value is weakref.ref:
            if len(args) > 1:
                callback = args[1]
            else:
                callback = variables.ConstantVariable.create(None)
            return variables.WeakRefVariable(args[0], callback)
        elif self.value is functools.partial:
            if not args:
                unimplemented(
                    gb_type="missing args to functools.partial",
                    context="",
                    explanation="functools.partial requires at least one argument",
                    hints=[
                        "Fix the functools.partial call.",
                        *graph_break_hints.USER_ERROR,
                    ],
                )
            # The first arg, a callable (the ctor below will assert on types)
            fn = args[0]
            rest_args = args[1:]
            # guards for the produced FunctoolsPartialVariable are installed in FunctoolsPartialVariable ctor from the
            # args and keywords
            return variables.functions.FunctoolsPartialVariable(
                fn, args=rest_args, keywords=kwargs
            )
        elif self.value is warnings.catch_warnings and not args:
            return variables.CatchWarningsCtxManagerVariable.create(tx, kwargs)
        elif self.value is torch.cuda.device and not kwargs and len(args) == 1:
            if not args[0].is_python_constant():
                raise_type_error(tx, "torch.cuda.device() requires a constant argument")
            return variables.CUDADeviceVariable.create(tx, args[0].as_python_constant())
        elif (
            issubclass(type(self.value), type)
            and hasattr(
                self.value, "__enter__"
            )  # TODO(voz): These can invoke user code!
            and hasattr(
                self.value, "__exit__"
            )  # TODO(voz): These can invoke user code!
            and self.is_standard_new()
            and SideEffects.cls_supports_mutation_side_effects(self.value)
            and self.source
            and not is_forbidden_context_manager(self.value)
        ):
            from . import TorchCtxManagerClassVariable
            from .functions import (
                BaseUserFunctionVariable,
                FunctionDecoratedByContextlibContextManagerVariable,
            )

            # graph break on any contextlib.* that it is not contextlib.contextmanager
            # Some of the APIs below are not supported because they rely on features
            # that Dynamo doesn't play well today (i.e. contextlib.suppress)
            if self.value in (
                contextlib._AsyncGeneratorContextManager,
                contextlib.closing,
                contextlib.redirect_stdout,
                contextlib.redirect_stderr,
                contextlib.AsyncExitStack,
            ):
                # We are not changing the behavior of Dynamo as these function were
                # already ignored on trace_rules.py before #136033 landed
                unimplemented(
                    gb_type="unsupported contextlib.* API",
                    context=f"{self.value}",
                    explanation=f"{self.value} not supported. This may be due to its use of "
                    "context-specific operations that are not supported in "
                    "Dynamo yet (i.e. Exception handling)",
                    hints=[
                        *graph_break_hints.SUPPORTABLE,
                    ],
                )
            arg_new = args
            if self.value is contextlib._GeneratorContextManager and isinstance(
                args[0], (BaseUserFunctionVariable, TorchCtxManagerClassVariable)
            ):
                if not torch._dynamo.config.enable_trace_contextlib:
                    unimplemented(
                        gb_type="attempted to trace contextlib.contextmanager",
                        context=f"args={args}",
                        explanation="Tracing contextlib.contextmanager is disabled.",
                        hints=[
                            "Set torch._dynamo.config.enable_trace_contextlib = True",
                        ],
                    )

                # Special treatments for certain context managers created via
                # contextlib, because
                # 1. we (pytorch) own their impls
                # 2. it's tedious to trace through them, so we effectively
                #    "allow in graph" them without sacrificing soundness.
                #
                # We would typically reach here via either
                # 1. the instance construction in `with ctx_manager(...):`:
                #    https://github.com/python/cpython/blob/3.12/Lib/contextlib.py#L301
                # 2. calling a function decorated with a context manager:
                #    https://github.com/python/cpython/blob/3.12/Lib/contextlib.py#L122
                #
                # So we basically trace through the surface part of the
                # contextlib code, and then special case the shared remaining
                # logic (the actual context manager instance construction and
                # usage later on).
                if isinstance(args[0], TorchCtxManagerClassVariable):
                    fn_var = args[0]
                    args_list = args[1].items  # type: ignore[union-attr,attr-defined]
                    kwargs_dict = args[2].keys_as_python_constant()  # type: ignore[union-attr,attr-defined]
                    return fn_var.call_function(tx, args_list, kwargs_dict)

                # Wrap UserFunctionVariable in FunctionDecoratedByContextlibContextManagerVariable
                # if the function is annotated with @contextlib.contextmanager
                # This shouldn't be necessary once generator functions are fully
                # supported in dynamo
                # pyrefly: ignore[unsupported-operation]
                arg_new = [
                    FunctionDecoratedByContextlibContextManagerVariable(
                        args[0], source=args[0].source
                    )
                ] + args[1:]

            return tx.inline_user_function_return(
                VariableTracker.build(
                    tx, polyfills.instantiate_user_defined_class_object
                ),
                [self, *arg_new],
                kwargs,
            )
        elif is_namedtuple_cls(self.value):
            if is_structseq_class(self.value):
                if kwargs or len(args) != 1:
                    raise_args_mismatch(
                        tx,
                        "torch.return_types",
                        "1 args and 0 kwargs",
                        f"{len(args)} args and {len(kwargs)} kwargs",
                    )
                # Structseq tp_new is a C function, so we can't trace into
                # it like namedtuples. Use track_new_user_defined_object
                # directly with self as both base_cls_vt and cls_vt.
                return tx.output.side_effects.track_new_user_defined_object(
                    self,
                    self,
                    list(args),
                )
            else:
                # Namedtuple __new__ is a Python function that calls
                # tuple.__new__(cls, (field_values,)). Let Dynamo trace
                # into it so default values and kwargs are handled by
                # the generated __new__ itself.
                return tx.inline_user_function_return(
                    VariableTracker.build(
                        tx, polyfills.instantiate_user_defined_class_object
                    ),
                    [self, *args],
                    kwargs,
                )
        elif self.value is torch.Size:
            # This simulates `THPSize_pynew`, the C impl for `Size.__new__`.
            from .lists import SizeVariable

            tup = SourcelessBuilder.create(tx, tuple).call_function(tx, args, kwargs)
            return SizeVariable(tup.items)  # type: ignore[missing-attribute]
        elif is_pydantic_dataclass_cls(self.value):
            # Pydantic populates dataclass fields through an external validator,
            # so tracing through the constructor misses the instance mutations.
            unimplemented(
                gb_type="Pydantic dataclass constructor",
                context=f"{self.value}",
                explanation="Dynamo graph breaks on pydantic dataclass constructors "
                "because validation mutates the instance outside traced bytecode.",
                hints=graph_break_hints.SUPPORTABLE,
            )
        elif (
            self.value in self._in_graph_classes()
            or is_traceable_wrapper_subclass_type(self.value)
        ):
            # torch.LongTensor cannot accept a list of FakeTensors.
            # So we stack the list of FakeTensors instead.
            from .lists import ListVariable

            if (
                np
                and self.value in tensortype_to_dtype
                and len(args) == 1
                and isinstance(args[0], ListVariable)
                and len(args[0].items) > 1
                and all(x.is_tensor() for x in args[0].items)
            ):
                # Stack FakeTensor
                stacked = wrap_fx_proxy(
                    tx=tx,
                    proxy=tx.output.create_proxy(
                        "call_function",
                        torch.stack,
                        *proxy_args_kwargs(args, kwargs),
                    ),
                )
                args = [stacked]

            if issubclass(self.value, torch.Stream):
                from .lists import TupleVariable

                var_kwargs = ConstDictVariable(
                    {VariableTracker.build(tx, k): v for k, v in kwargs.items()}
                )
                var_args = TupleVariable(list(args))
                stream = self.value(
                    *(var_args.as_python_constant()),
                    **(var_kwargs.as_python_constant()),
                )
                from ..graph_bytecode_inputs import register_graph_created_object
                from .streams import StreamVariable

                ind = register_graph_created_object(
                    stream,
                    StreamVariable.make_construct_in_graph_stream_fn(
                        var_args, var_kwargs
                    ),
                )
                tensor_variable = wrap_fx_proxy(
                    tx=tx,
                    proxy=tx.output.create_proxy(
                        "call_function", get_external_object_by_index, (ind,), {}
                    ),
                )
            elif issubclass(self.value, torch.Event):
                from .lists import TupleVariable

                # Register newly created event for reconstruction
                var_kwargs = ConstDictVariable(
                    {VariableTracker.build(tx, k): v for k, v in kwargs.items()}
                )
                var_args = TupleVariable(list(args))
                event = self.value(
                    *(var_args.as_python_constant()),
                    **(var_kwargs.as_python_constant()),
                )
                from ..graph_bytecode_inputs import register_graph_created_object
                from .streams import EventVariable

                ind = register_graph_created_object(
                    event,
                    EventVariable.make_construct_in_graph_event_fn(
                        var_args, var_kwargs
                    ),
                )
                tensor_variable = wrap_fx_proxy(
                    tx=tx,
                    proxy=tx.output.create_proxy(
                        "call_function", get_external_object_by_index, (ind,), {}
                    ),
                )
            else:
                tensor_variable = wrap_fx_proxy(
                    tx=tx,
                    proxy=tx.output.create_proxy(
                        "call_function",
                        self.value,
                        *proxy_args_kwargs(args, kwargs),
                    ),
                )

            return tensor_variable
        elif self.value is random.Random:
            if len(args) == 1 and args[0].is_python_constant():
                seed = args[0].as_python_constant()
            else:
                seed = None
            random_object = random.Random(seed)
            return RandomVariable(random_object)
        elif self.value is types.MappingProxyType and len(args) == 1:
            # types.MappingProxyType is a read-only proxy of the dict. If the
            # original dict changes, the changes are reflected in proxy as well.
            dict_arg = args[0]
            if isinstance(dict_arg, variables.UserDefinedDictVariable):
                dict_arg = dict_arg._base_vt
            if isinstance(dict_arg, ConstDictVariable):
                return variables.MappingProxyVariable(dict_arg)
        elif SideEffects.cls_supports_mutation_side_effects(self.value) and self.source:
            with do_not_convert_to_tracable_parameter():
                result = tx.inline_user_function_return(
                    VariableTracker.build(
                        tx, polyfills.instantiate_user_defined_class_object
                    ),
                    [self, *args],
                    kwargs,
                )
                return result

        return super().call_function(tx, args, kwargs)