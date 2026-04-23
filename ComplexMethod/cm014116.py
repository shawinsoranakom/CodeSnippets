def _wrap(self, value: Any) -> VariableTracker:
        # import here to avoid circular dependencies
        from torch.utils._triton import (
            has_triton,
            has_triton_experimental_host_tma,
            has_triton_tensor_descriptor_host_tma,
        )

        from ..decorators import (
            CudagraphOverrideContextManager,
            DynamoConfigPatchProxy,
            ErrorOnGraphBreakDecoratorContextManager,
        )

        if has_triton():
            from triton.runtime.autotuner import Autotuner
            from triton.runtime.jit import JITFunction
        else:

            class JITFunction:
                pass

            class Autotuner:
                pass

        # default implementations, in case we don't have triton (or the wrong triton version)
        def create_1d_tma_descriptor() -> None:
            pass

        def create_2d_tma_descriptor() -> None:
            pass

        class TensorDescriptor:
            @staticmethod
            def from_tensor() -> None:
                pass

        def set_allocator() -> None:
            pass

        if has_triton_experimental_host_tma():
            from triton.tools.experimental_descriptor import (
                create_1d_tma_descriptor,
                create_2d_tma_descriptor,
            )
        if has_triton_tensor_descriptor_host_tma():
            from triton.tools.tensor_descriptor import TensorDescriptor
        if has_triton():
            import triton as triton_mod

            if hasattr(triton_mod, "set_allocator"):
                set_allocator = triton_mod.set_allocator

        # Handle exact type() match
        type_dispatch = self._type_dispatch().get(type(value))
        if type_dispatch is not None:
            return type_dispatch(self, value)

        # Handle exact id() match
        id_dispatch = self._id_dispatch().get(id(value))
        if id_dispatch is not None:
            return id_dispatch(self, value)

        # Everything else (NB: order matters!)
        if (
            isinstance(value, torch.Tensor)
            and type(value)
            not in (
                # These torch-native subclasses have overly restrictive
                # `__torch_function__` which prevents Dynamo from reading their
                # tensor attributes like `is_nested` or calling methods like
                # `_is_view`.
                torch.nn.parameter.UninitializedBuffer,
                torch.nn.parameter.UninitializedParameter,
                ExpandedWeight,
            )
            and type(value) not in config.nontraceable_tensor_subclasses
        ):
            if (
                type(value).__torch_dispatch__ is torch.Tensor.__torch_dispatch__
                or is_traceable_wrapper_subclass(value)
            ):
                return self.wrap_tensor(value)

        if is_namedtuple(value):
            self.install_guards(GuardBuilder.SEQUENCE_LENGTH)
            output: list[VariableTracker] = [
                LazyVariableTracker.create(
                    getattr(value, name),
                    source=AttrSource(self.source, name),
                )
                for name in namedtuple_fields(type(value))
            ]

            tuple_vt = TupleVariable(
                output,
                source=self.source,
                mutation_type=ValueMutationExisting(),
            )
            result = UserDefinedTupleVariable.get_vt_cls(type(value))(
                value,
                source=self.source,
                tuple_vt=tuple_vt,
            )
            return self.tx.output.side_effects.track_object_existing(value, result)
        elif istype(value, (dict, collections.defaultdict, collections.OrderedDict)):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            all_const = all(ConstantVariable.is_literal(k) for k in value)

            # For all_const, we don't have to guard on anything yet. We guard on
            # keys lazily by adding a dict_getitem entry for each accessed key.
            # For cases where we need to guard on all keys, we lazily put guards
            # during the dict call_method (check dicts.py)
            if not all_const:
                # Guard on the key order
                # This is not ideal, i.e., there is no need to guard on the key
                # order. But we guard on the key order because of the complexity
                #
                # 1) For non-constant objects, we can't save the key in the
                # guard context because it can be memory heavy. We can add
                # weakrefs but this complicates the accesses.
                #
                # 2) For non-constant objects, we also have to guard on the keys
                # (like TENSOR_MATCH on tensor). We might also have guards on
                # the attributes of the keys (like tensor.grad). To make this
                # work in tree structure is complicated.
                #
                # So, instead we guard on the key order. While guarding on key
                # order, we just save the indices and use it to access keys and
                # values. Indices are cheap to save.
                self.tx.output.guard_on_key_order.add(self.source)

            # We need all the keys to be hashable. We do this within the
            # HashableTracker class in hashable.py
            def build_key_value(
                i: Any, k: Any, v: Any
            ) -> tuple[VariableTracker, VariableTracker]:
                base = self.get_source()
                if all_const:
                    key = ConstantVariable.create(k)
                    source_key = k
                else:
                    source_key = ConstDictKeySource(base, i)
                    key = LazyVariableTracker.create(k, source_key)
                source_value = DictGetItemSource(base, source_key)
                res_value = LazyVariableTracker.create(v, source_value)

                return key, res_value

            result = dict(
                build_key_value(i, k, v)
                for i, k, v in enumerate_items_with_dict_position(value)
            )

            if istype(value, collections.defaultdict):
                factory_source = AttrSource(self.source, "default_factory")
                dict_vt = ConstDictVariable(
                    result,  # type: ignore[arg-type]
                    mutation_type=ValueMutationExisting(),
                    source=self.source,
                )
                result = DefaultDictVariable(
                    value,
                    default_factory=VariableBuilder(self.tx, factory_source)(
                        value.default_factory
                    ),
                    dict_vt=dict_vt,
                    source=self.source,
                )
                return self.tx.output.side_effects.track_object_existing(value, result)
            elif istype(value, collections.OrderedDict):
                dict_vt = ConstDictVariable(
                    result,  # type: ignore[arg-type]
                    user_cls=collections.OrderedDict,
                    mutation_type=ValueMutationExisting(),
                    source=self.source,
                )
                result = OrderedDictVariable(value, dict_vt=dict_vt, source=self.source)
                return self.tx.output.side_effects.track_object_existing(value, result)
            else:
                result = ConstDictVariable(
                    result,  # type: ignore[arg-type]
                    source=self.source,
                )

            return self.tx.output.side_effects.track_mutable(value, result)
        elif isinstance(value, torch.nn.Module):
            return self.wrap_module(value)
        elif ConstantVariable.is_literal(value):  # non-atomic literals
            return self.wrap_literal(value)
        elif isinstance(value, torch.overrides.TorchFunctionMode):
            var = TorchFunctionModeVariable(value, source=self.source)
            self.tx.output.side_effects.track_object_existing(value, var)
            return var
        elif istype(value, (set, OrderedSet)):
            if any(isinstance(x, torch.Tensor) for x in value):
                unimplemented(
                    gb_type="Attempted to wrap a set with tensors",
                    context="Python set containing torch.Tensor elements",
                    explanation=(
                        "Dynamo cannot trace sets of tensors. To get a stable ordering, "
                        "Dynamo needs to convert the set into a list and the order might not be "
                        "stable if the set contains tensors."
                    ),
                    hints=[
                        "Use a dictionary where the keys are tensors.",
                        *graph_break_hints.SUPPORTABLE,
                    ],
                )

            self.install_guards(GuardBuilder.TYPE_MATCH)
            self.install_guards(GuardBuilder.SEQUENCE_LENGTH)
            set_var_cls = SetVariable

            if istype(value, OrderedSet):
                # Guard on the internal dict of OrderedSet
                internal_dict_source = AttrSource(self.source, "_dict")
                install_guard(
                    internal_dict_source.make_guard(GuardBuilder.DICT_KEYS_MATCH)
                )
                self.tx.output.guard_on_key_order.add(internal_dict_source)
                set_var_cls = OrderedSetVariable

            # The list gives a ordering for the set items. The ordering is based
            # on the Python hash and it is not related to object ordering inside
            # the set object. The order being incorrect at runtime will lead to
            # a recompilation.
            L = list(value)
            items = [
                LazyVariableTracker.create(
                    v, source=NonSerializableSetGetItemSource(self.source, i)
                )
                for i, v in enumerate(L)
            ]
            result = set_var_cls(items, source=self.source)
            return self.tx.output.side_effects.track_object_existing(value, result)
        elif istype(value, frozenset) and all(
            (
                # For DBR quantization, we could get a frozenset of torch funcs.
                (type(x) is types.BuiltinMethodType and x.__module__ == "torch")
                or
                # Another commonly used frozenset of types.
                x in torch.utils._pytree.BUILTIN_TYPES
                or
                # For activation checkpointing, we could get a frozenset of torch ops.
                isinstance(x, (OpOverload, OpOverloadPacket))
            )
            for x in value
        ):
            # For the limited cases of frozenset here, we know the items won't
            # change across runs, so we can safely create sourceless VTs for
            # them and guard on the frozenset contents via EQUALS_MATCH.
            # TODO support source for sets and remove the special logics here.
            items = [SourcelessBuilder.create(self.tx, v) for v in value]
            self.install_guards(GuardBuilder.EQUALS_MATCH)
            return FrozensetVariable(items, source=self.source)
        elif isinstance(
            value,
            (enum.Enum, torch.DispatchKey, torch._C._functorch.TransformType),
        ) or is_pybind11_enum_member(value):
            self.install_guards(GuardBuilder.ID_MATCH)
            return UserDefinedObjectVariable(value, source=self.source)
        elif DebuggingVariable.is_reorderable_logging_function(value):
            # Put this above builtin_callable so that print() can be handled
            # along with other builtin debugging functions
            self.install_guards(GuardBuilder.BUILTIN_MATCH)
            return DebuggingVariable(value, source=self.source)
        elif callable(value) and any(
            value is fn for fn in torch._dynamo.config.ignore_logging_functions
        ):
            # Treat ignored functions as full no-ops
            self.install_guards(GuardBuilder.ID_MATCH)
            return IgnoredFunctionVariable(value, source=self.source)
        elif isinstance(value, logging.Logger):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            return LoggingLoggerVariable(value, source=self.source)
        elif is_utils_checkpoint(value):
            return build_checkpoint_variable(source=self.source)
        elif is_invoke_subgraph(value):
            return build_invoke_subgraph_variable(source=self.source)
        elif LocalMapWrappedHigherOrderVariable.should_wrap_in_hop(value):
            return LocalMapWrappedHigherOrderVariable.build(source=self.source)
        elif isinstance(value, functools.partial):
            func_src = AttrSource(self.get_source(), "func")
            func_obj = VariableBuilder(self.tx, func_src)(value.func)

            args = []
            args_source = AttrSource(self.get_source(), "args")
            for i, arg in enumerate(value.args):
                args.append(
                    VariableBuilder(self.tx, GetItemSource(args_source, i))(arg)
                )

            keywords = {}
            keywords_source = AttrSource(self.get_source(), "keywords")
            for k, v in value.keywords.items():
                if not ConstantVariable.is_literal(k):
                    unimplemented(
                        gb_type="functools.partial() with non-literal keyword",
                        context=f"non-literal keyword: {k}",
                        explanation="functools.partial() expects literal/string keywords",
                        hints=[*graph_break_hints.USER_ERROR],
                    )
                keywords[k] = VariableBuilder(
                    self.tx, DictGetItemSource(keywords_source, k)
                )(v)

            install_guard(
                self.get_source().make_guard(GuardBuilder.TYPE_MATCH),
                keywords_source.make_guard(GuardBuilder.DICT_KEYS_MATCH),
                args_source.make_guard(GuardBuilder.SEQUENCE_LENGTH),
            )
            # Preserve cache_hash for SAC context_fn caching
            original_cache_hash = getattr(value, "cache_hash", None)
            return FunctoolsPartialVariable(
                func_obj, args, keywords, original_cache_hash=original_cache_hash
            )
        elif is_typing(value):
            # typing.List, typing.Mapping, etc.
            self.install_guards(GuardBuilder.ID_MATCH)
            return TypingVariable(
                value,
                source=self.source,
            )
        elif np is not None and isinstance(value, np.generic):
            # numpy array scalars: convert to 0D arrays
            return self.wrap_numpy_ndarray(np.asarray(value))
        elif trace_rules.is_numpy(value):
            assert np
            if istype(value, types.MethodType):
                # Dont guard on cython functions as they dont change ids
                if inspect.isfunction(value.__func__):
                    install_guard(
                        AttrSource(self.source, "__func__").make_guard(
                            GuardBuilder.CLOSURE_MATCH
                        )
                    )
            elif inspect.isclass(value):
                self.install_guards(GuardBuilder.CLASS_MATCH)
            elif inspect.isfunction(value):
                self.install_guards(GuardBuilder.CLOSURE_MATCH)
            elif callable(value):
                self.install_guards(GuardBuilder.ID_MATCH)
            else:
                self.install_guards(GuardBuilder.TYPE_MATCH)
            return NumpyVariable(value, source=self.source)
        elif trace_rules.is_numpy_dtype(value):
            self.install_guards(GuardBuilder.ID_MATCH)
            return NumpyDTypeVariable(value, source=self.source)
        elif trace_rules.is_numpy_type_info(value):
            if isinstance(value, np.iinfo):
                self.install_guards(GuardBuilder.TYPE_MATCH)
                dt_source = AttrSource(self.source, "dtype")
                install_guard(dt_source.make_guard(GuardBuilder.ID_MATCH))
            else:
                self.install_guards(GuardBuilder.ID_MATCH)
            return ConstantLikeVariable(value, source=self.source)
        # NB: These can't be put in type_dispatch, they have to run later
        elif CollectiveFunctionRewriteVariable.can_rewrite(value):
            self.install_guards(GuardBuilder.CLOSURE_MATCH)
            return CollectiveFunctionRewriteVariable.create(
                self.tx,
                value,
                source=self.source,
            )
        elif istype(value, torch.autograd.function.FunctionMeta):
            self.install_guards(GuardBuilder.CLASS_MATCH)
            return AutogradFunctionVariable(
                value,
                source=self.source,
            )
        elif isinstance(value, torch.autograd.function.FunctionCtx):
            actual_saved_tensors = None
            try:
                # type: ignore[attr-defined]
                actual_saved_tensors = value.saved_tensors
            except RuntimeError:
                pass

            saved_tensors = []
            guards = [self.source.make_guard(GuardBuilder.TYPE_MATCH)]
            if isinstance(actual_saved_tensors, tuple):
                saved_tensors_source = AttrSource(self.source, "saved_tensors")
                guards.append(
                    saved_tensors_source.make_guard(GuardBuilder.SEQUENCE_LENGTH)
                )
                for i, v in enumerate(actual_saved_tensors):
                    saved_tensors.append(
                        VariableBuilder(
                            self.tx, GetItemSource(saved_tensors_source, i)
                        )(v)
                    )
            install_guard(*guards)

            return self.tx.output.side_effects.track_object_existing(
                value,
                AutogradFunctionContextVariable(
                    value,
                    source=self.source,
                    saved_tensors=SavedTensorBox(saved_tensors),
                ),
            )
        elif (
            isinstance(value, types.MethodType)
            and istype(
                getattr(value, "__self__", None), torch.autograd.function.FunctionMeta
            )
            and getattr(value, "__name__", "") == "apply"
            and value == getattr(value.__self__, "apply", None)
        ):
            # handle aliased autograd function `apply` calls
            install_guard(
                AttrSource(self.get_source(), "__func__").make_guard(
                    GuardBuilder.CLOSURE_MATCH
                )
            )
            return GetAttrVariable(
                AutogradFunctionVariable(
                    value.__self__,
                    source=AttrSource(self.source, member="__self__"),
                ),
                "apply",
                py_type=type(value),
            )
        elif isinstance(value, torch._C._ImperativeEngine):
            self.install_guards(GuardBuilder.ID_MATCH)
            return AutogradEngineVariable(value, source=self.source)
        elif (
            value
            is torch._dynamo.external_utils.FakeCompiledAutogradEngine._exec_final_callbacks_stub
        ):
            self.install_guards(GuardBuilder.CLOSURE_MATCH)
            return LambdaVariable(
                lambda: UserFunctionVariable(
                    torch._dynamo.external_utils.FakeCompiledAutogradEngine.exec_final_callbacks,
                ).call_function(
                    self.tx,
                    (self.tx.output.side_effects.get_ca_final_callbacks_var(),),
                    {},
                )
            )
        elif isinstance(value, DynamoConfigPatchProxy):
            return DynamoConfigPatchVariable(value.changes)
        elif isinstance(value, ErrorOnGraphBreakDecoratorContextManager):
            return ErrorOnGraphBreakVariable(value.error_on_graph_break)
        elif isinstance(value, CudagraphOverrideContextManager):
            return CudagraphOverrideVariable(value.fwd, value.bwd)
        elif callable(value) and trace_rules.lookup_callable(value) is not None:
            if trace_rules.is_callable_allowed(value):
                self.tx.output.has_user_defined_allowed_in_graph = True
            # type: ignore[attr-defined]
            return trace_rules.lookup_callable(value).create_with_source(
                value, source=self.source
            )
        elif np and isinstance(value, np.number):
            return self.wrap_unspecialized_primitive(value)
        elif isinstance(value, HigherOrderOperator):
            if value is torch._higher_order_ops.invoke_subgraph:
                unimplemented(
                    gb_type="Attempted to wrap torch._higher_order_ops.invoke_subgraph",
                    context="",
                    explanation="Directly using invoke_subgraph is not supported. Use nested_compile_region",
                    hints=[],
                )
            self.install_guards(GuardBuilder.TYPE_MATCH)
            return TorchHigherOrderOperatorVariable.make(value, source=self.source)
        elif isinstance(value, torch.cuda.StreamContext):
            self.install_guards(GuardBuilder.ID_MATCH)
            stream_source = AttrSource(self.source, "stream")
            stream_var = VariableBuilder(self.tx, stream_source)(value.stream)
            # type: ignore[arg-type]
            return StreamContextVariable.create(self.tx, stream_var)
        elif isinstance(value, torch.Stream):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            if isinstance(self.source, CurrentStreamSource):
                # Reuse the index pre-allocated in SymbolicStreamState.__init__
                index = CURRENT_STREAM_INDEX
            else:
                index = register_user_object(value, self.source)
            stream_proxy = self.tx.output.create_proxy(
                "call_function", get_external_object_by_index, (index,), {}
            )
            set_example_value(stream_proxy.node, value)
            var = StreamVariable(
                stream_proxy, value, source=self.source, user_object_index=index
            )
            return self.tx.output.side_effects.track_object_existing(value, var)
        elif isinstance(value, (torch._C._SDPAParams)):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            return SDPAParamsVariable.create(self.tx, value, self.source)
        elif isinstance(value, torch._functorch.pyfunctorch.FuncTorchInterpreter):
            self.install_guards(GuardBuilder.ID_MATCH)
            return FuncTorchInterpreterVariable(value)
        elif isinstance(value, torch.Event):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            index = register_user_object(value, self.source)
            event_proxy = self.tx.output.create_proxy(
                "call_function",
                get_external_object_by_index,
                (index,),
                {},
            )
            set_example_value(event_proxy.node, value)
            return EventVariable(
                event_proxy,
                value,
                index,
                source=self.source,
            )
        elif (
            istype(value, contextlib.nullcontext)
            and inspect.getattr_static(value, "enter_result", None) is None
        ):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            return NullContextVariable(source=self.source)
        elif KeyedJaggedTensorVariable.is_matching_object(value):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            result = KeyedJaggedTensorVariable(value, source=self.source)
            # TODO: this doing it manually is bad
            return self.tx.output.side_effects.track_object_existing(value, result)
        elif isinstance(value, torch.optim.Optimizer):
            self.install_guards(GuardBuilder.ID_MATCH)
            self.source = OptimizerSource(self.source)
            return OptimizerVariable(
                value,
                source=self.source,
                mutation_type=AttributeMutationExisting(),
            )
        elif isinstance(value, torch.DispatchKeySet):
            self.install_guards(GuardBuilder.DISPATCH_KEY_SET_MATCH)
            return DispatchKeySetVariable(value)
        elif WorldMetaClassVariable.is_group_member_type(value):
            return WorldMetaClassVariable(value, source=self.source)
        elif value is OrderedSet:
            self.install_guards(GuardBuilder.ID_MATCH)
            return OrderedSetClassVariable()
        elif (
            id(value) in ITERTOOLS_TYPE_IDS
            and id(value) not in ITERTOOLS_POLYFILLED_TYPE_IDS
        ):
            self.install_guards(GuardBuilder.CLASS_MATCH)
            return ItertoolsVariable(value, source=self.source)
        elif isinstance(value, _DynamicScalar):
            is_int = isinstance(value, DynamicInt)
            source = DynamicScalarSource(self.source, is_int)
            if id(value) in self.tx.output.root_tracer.dynamic_scalar_nodes:
                # If we've already seen this dynamic scalar, reuse the existing
                # SymInt/SymFloat node.
                node = self.tx.output.root_tracer.dynamic_scalar_nodes[id(value)]
            else:
                sym = self.tx.output.shape_env.create_unspecified_symbol(
                    value.real,  # type: ignore[attr-defined]
                    source=source,
                    dynamic_dim=DimDynamic.DYNAMIC,
                )
                node = self.tx.output.shape_env.create_symintnode(
                    sym,
                    hint=value.real,  # type: ignore[attr-defined]
                    source=source,
                )
                if not isinstance(node, SymInt):
                    raise AssertionError(f"Expected SymInt, got {type(node)}")

            # Bind to graph input
            sym_node_proxy = self.tx.output.root_tracer.create_graph_input(
                re.sub(r"[^a-zA-Z0-9]+", "_", self.name),
                type(node),
                node,
                source=source,
            )
            sym_node_proxy.node.meta["grapharg"] = GraphArg(
                source,
                node,
                False,
                None,
                is_tensor=False,
                example_strong_ref=node,
            )
            sym_expr = node.node.expr
            assert isinstance(sym_expr, sympy.Symbol), (
                f"{sym_expr} is not a basic Symbol."
            )
            self.tx.output.tracked_fakes.append(TrackedFake(node, source, None))
            return SymNodeVariable.create(self.tx, sym_node_proxy, node)
        elif is_torch_sym(value):
            # Note: this doesn't handle nested symints.
            # For SymBool input, we reuse the infra for SymInt by simulating SymBool with a SymInt in dynamo.

            # Concretely,
            # 1. We create a SymInt in dynamo's shape_env, whose source is constructed as ConvertIntSource(self.source).
            # so that guards on the SymInts can be effectively applied on the original SymBool in user program.
            # 2. We create a SymBool based on the SymInt in dynamo's ShapeEnv. Because the original user program
            # depends on the value being a SymBool. This allows dynamo to interpret the user's program correctly.
            source = (
                self.source
                if isinstance(value, torch.SymInt)
                else ConvertIntSource(self.source)
            )
            new_symint = None
            if value.node.has_hint():
                new_symint = (
                    self.tx.output.shape_env.create_unspecified_symint_and_symbol(
                        int(value.node.hint),
                        source,
                        dynamic_dim=DimDynamic.DYNAMIC,
                    )
                )
            else:
                if isinstance(value, torch.SymBool):
                    # We need to create an unbacked symint to replace the unbacked symbool.
                    new_symint = self.tx.output.shape_env.create_unbacked_symint()
                else:
                    # TODO (yidi): we need to figure out a way to propagate the guards
                    # we accumulated when tracing the subggraph to outer shape_env. For normal symints,
                    # this is automatically done by evaluating the guards once but this
                    # will cause data-dependent error when we evaluate the outer unbacked symints.
                    # The test case that triggers this graph break is test_cond_unbacked_symint_closure
                    unimplemented(
                        gb_type="Attempted to wrap unbacked SymInt",
                        context="",
                        explanation="Unbacked SymInt input is not supported yet.",
                        hints=[*graph_break_hints.SUPPORTABLE],
                    )
            assert new_symint is not None
            if not isinstance(new_symint, SymInt):
                raise AssertionError(f"Expected SymInt, got {type(new_symint)}")
            sym_node_proxy = self.tx.output.root_tracer.create_graph_input(
                re.sub(r"[^a-zA-Z0-9]+", "_", self.name),
                type(new_symint),
                new_symint,
                source=source,
            )

            sym_node_proxy.node.meta["grapharg"] = GraphArg(
                source,
                new_symint,
                False,
                None,
                is_tensor=False,
                example_strong_ref=new_symint,
            )
            # We bind the new_symint to graph input.
            sym_expr = new_symint.node.expr
            assert isinstance(sym_expr, sympy.Symbol), (
                f"{sym_expr} is not a basic Symbol."
            )
            self.tx.output.tracked_fakes.append(TrackedFake(new_symint, source, None))

            tracing_symint = (
                new_symint if isinstance(value, torch.SymInt) else new_symint == 1
            )  # cast it back to symbool for tracing
            return SymNodeVariable(sym_node_proxy, tracing_symint)

        elif isinstance(value, (JITFunction, Autotuner)):
            self.install_guards(GuardBuilder.ID_MATCH)
            return TritonKernelVariable(
                value,
                None,  # No kernel idx provided
                None,  # No grid provided
                source=self.source,
            )
        elif value is create_1d_tma_descriptor:
            return CreateTMADescriptorExperimentalVariable(rank=1)
        elif value is create_2d_tma_descriptor:
            return CreateTMADescriptorExperimentalVariable(rank=2)
        elif value is TensorDescriptor.from_tensor:
            return CreateTMADescriptorStableVariable()
        elif value is set_allocator:
            return TritonSetAllocatorVariable(value)
        elif isinstance(value, torch.amp.autocast_mode.autocast):
            if isinstance(value, torch.amp.autocast_mode._UnmanagedAutocast):
                return self.wrap_user_defined(value)
            else:
                self.install_guards(GuardBuilder.ID_MATCH)
                return AutocastModeVariable(
                    target_values=[
                        value.device,
                        value.fast_dtype,
                        value._enabled,
                        value._cache_enabled,
                    ],
                    source=self.source,
                )
        elif TorchCtxManagerClassVariable.is_matching_cls(value):
            if inspect.isclass(value):
                self.install_guards(GuardBuilder.CLASS_MATCH)
            elif inspect.isfunction(value):
                self.install_guards(GuardBuilder.CLOSURE_MATCH)
            return TorchCtxManagerClassVariable(value, source=self.source)
        elif inspect.getattr_static(value, "__script_if_tracing_wrapper", False):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            return WrapperUserFunctionVariable(
                value,
                "__original_fn",
                source=self.source,
                mutation_type=AttributeMutationExisting(),
            )
        elif is_lru_cache_wrapped_function(value):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            return WrapperUserFunctionVariable(
                value,
                "__wrapped__",
                source=self.source,
                mutation_type=AttributeMutationExisting(),
            )
        elif value is sys.exc_info or (
            sys.version_info >= (3, 11) and value is sys.exception
        ):
            return SysFunctionVariable(value, source=self.source)
        elif is_function_or_wrapper(value) and inspect.getattr_static(
            value, "_torchdynamo_inline", False
        ):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            return WrapperUserFunctionVariable(
                value,
                "_torchdynamo_inline",
                source=self.source,
                mutation_type=AttributeMutationExisting(),
            )
        elif value is collections.namedtuple:
            self.install_guards(GuardBuilder.ID_MATCH)
            return CollectionsNamedTupleFunction(value, source=self.source)
        elif isinstance(
            value, types.BuiltinMethodType
        ) and BuiltinMethodVariable.is_supported_builtin_method(value):
            self.install_guards(GuardBuilder.ID_MATCH)
            return BuiltinMethodVariable(value, source=self.source)
        elif is_function(value) and value in (float.fromhex, float.hex):
            self.install_guards(GuardBuilder.ID_MATCH)
            return GetAttrVariable(
                BuiltinVariable(float, source=self.source),
                value.__name__,
                py_type=type(value),
            )
        elif is_function_or_wrapper(value):
            value, attr_name = unwrap_with_attr_name_if_wrapper(value)
            # For these wrappers, Dynamo points to the wrapped function,
            # so source needs to be updated as well.
            if attr_name is not None:
                self.source = AttrSource(self.source, attr_name)
            # type: ignore[attr-defined]
            return trace_rules.lookup(value).create_with_source(
                value, source=self.source
            )
        elif value is random.Random:
            self.install_guards(GuardBuilder.ID_MATCH)
            return RandomClassVariable(source=self.source)
        elif istype(value, random.Random) and RandomVariable.is_supported_random_obj(
            value
        ):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            result = RandomVariable(value, source=self.source)
            self.tx.output.side_effects.track_mutable(value, result)
            return result
        # Don't use istype, since some python modules are not subclasses of types.ModuleType directly.
        # E.g, type(torch.ops) -> <class 'torch._ops._Ops'>,
        # type(torch.backends.cudnn) -> <class 'torch.backends.cudnn.CudnnModule'>
        elif isinstance(value, (types.ModuleType, replay_record.DummyModule)):
            self.install_guards(GuardBuilder.MODULE_MATCH)
            result = PythonModuleVariable(
                # type: ignore[arg-type]
                value,
                source=self.source,
            )
            self.tx.output.side_effects.track_object_existing(value, result)
            return result
        elif isinstance(value, types.GetSetDescriptorType):
            # GetSet descriptors are C functions attached to an attribute lookup
            # using PyGetSetDef. Python, on attribute lookup, can decide to
            # create a new object on the fly, and therefore the `id` of the
            # descriptors is not guaranteed to be same for different attribute
            # accesses. Since these are unlikely to change during the program
            # execution, we can skip guarding on them.
            return GetSetDescriptorVariable(value)
        elif isinstance(value, types.MethodWrapperType):
            # Method-wrappers are written in C, and they are not guaranteed to
            # return the same object on attribute lookup. Therefore, we cannot
            # insert a ID_MATCH guard here. method-wrappers are very
            # unlikely to change, so its ok to skip the guard here.
            return MethodWrapperVariable(value)
        elif issubclass(type(value), type) and issubclass(value, BaseException):
            # match user defined exceptions
            self.install_guards(GuardBuilder.ID_MATCH)
            return UserDefinedExceptionClassVariable(value)
        elif issubclass(type(value), type):
            if value in (
                torch.utils.hooks.BackwardHook,
                torch.nn.Parameter,
                torch.nn.Buffer,
            ):
                # TODO(jansel): combine this case with the one above
                # type: ignore[attr-defined]
                return trace_rules.lookup(value).create_with_source(
                    value, source=self.source
                )
            if value is torch.autograd._unsafe_preserve_version_counter:
                self.install_guards(GuardBuilder.CLASS_MATCH)
                return PreserveVersionContextVariable.constructor(self.tx)
            if (
                # `value` must be a strict subclass of `torch.Tensor`
                issubclass(value, torch.Tensor)
                and value is not torch.Tensor
                # `TensorSubclassVariable` is not for subclass that overrides
                # `torch_dispatch`.
                and value.__torch_dispatch__ is torch.Tensor.__torch_dispatch__
                # `TensorSubclassVariable` would lead to construction of
                # `TensorWithTFOverrideVariable`, but we don't want that for
                # traceable wrapper subclasses (we wrap those subclass instances
                # into `TensorVariable`).
                and not is_traceable_wrapper_subclass_type(value)
            ):
                return TensorSubclassVariable(value, source=self.source)

            if not is_from_closure_source(self.source):
                # For closure source, the variable comes from LOAD_SUPER_ATTR,
                # which calls self.__class__. This is internal Cpython
                # implementation, and it is rare for the user to modify
                # self.__class__ manually.
                # For other cases, this is a userdefined class, so install an
                # ID_MATCH even if its a global variable.
                self.install_guards(GuardBuilder.CLASS_MATCH)

            if isinstance(value, type) and issubclass(value, enum.Enum):
                return UserDefinedClassVariable(
                    value,
                    source=self.source,
                )

            if is_opaque_type(value):
                return OpaqueObjectClassVariable(
                    value,
                    source=self.source,
                )

            return UserDefinedClassVariable(
                value,
                source=self.source,
            )
        elif TorchScriptObjectVariable.is_matching_cls(type(value)):
            from ..source import (
                FlattenScriptObjectSource,
                ScriptObjectQualifiedNameSource,
            )

            # Unwrap FakeScriptObject to the underlying real object so the
            # rest of this branch (guards, graph inputs, etc.) operates on
            # the real opaque object type.
            if isinstance(value, torch._library.fake_class_registry.FakeScriptObject):
                value = value.real_obj

            # type: ignore[arg-type]
            if torch._library.fake_class_registry.tracing_with_real(value):
                proxy = self.tx.output.root_tracer.create_graph_input(
                    re.sub(r"[^a-zA-Z0-9]+", "_", self.name),
                    type(value),
                    value,
                    source=self.source,
                )

                # setting is_unspecialized=False to not insert a as_tensor call in reconstruct by default
                # setting example to be real value because these example values will be used
                # as example_inputs for user compiler.
                proxy.node.meta["grapharg"] = GraphArg(
                    self.source,
                    value,
                    False,
                    None,
                    False,
                    value,  # type: ignore[arg-type]
                )
                return TorchScriptObjectVariable.create(
                    proxy,
                    value,
                    source=self.source,
                )

            if is_opaque_value_type(type(value)):
                # Value-type: guard on equality (will use __eq__)
                self.install_guards(GuardBuilder.CONSTANT_MATCH)
            elif is_opaque_reference_type(type(value)):
                # Reference-type: guard only on type, and registered guard_fn
                self.install_guards(GuardBuilder.TYPE_MATCH)
                self.install_guards(GuardBuilder.OPAQUE_OBJ_GUARD_FN_MATCH)
            elif not hasattr(value, "__obj_flatten__"):
                # This exists to allow a smoother transition.
                # The implications are:
                # The script objects won't be tracked as proxies.
                # Methods on these objects won't show up in the graph.
                # The original script object might be mutated.
                return self.wrap_user_defined(value)
            else:
                # Install the guards on the fully qualified name of the script object
                LazyVariableTracker.realize_all(
                    VariableBuilder(
                        self.tx, ScriptObjectQualifiedNameSource(self.source)
                    )(
                        value._type().qualified_name()  # type: ignore[attr-defined]
                    )
                )
                # Install the guards on the content of the script object by setting the source
                # to be FlattenScriptObjectSource, which calls __obj_flatten__() to get the contents.
                LazyVariableTracker.realize_all(
                    VariableBuilder(self.tx, FlattenScriptObjectSource(self.source))(
                        value.__obj_flatten__()
                    )
                )

            fake_script_obj = torch._library.fake_class_registry.maybe_to_fake_obj(
                self.tx.output.fake_mode, value
            )
            if is_opaque_value_type(type(value)) and not should_hoist(type(value)):
                fake_script_obj = value
                proxy = value

            elif config.install_free_tensors and (
                is_from_global_source(self.source)
                or is_from_nonlocal_source(self.source)
                or is_from_unspecialized_nn_module_source(self.source)
            ):
                return self.tx.output.register_attr_or_module(
                    value, self.name, source=self.source
                )

            else:
                proxy = self.tx.output.root_tracer.create_graph_input(
                    re.sub(r"[^a-zA-Z0-9]+", "_", self.name),
                    type(value),
                    fake_script_obj,
                    source=self.source,
                )
                # setting is_unspecialized=False to not insert a as_tensor call in reconstruct by default
                # setting example to be real value because these example values will be used
                # as example_inputs for user compiler.
                proxy.node.meta["grapharg"] = GraphArg(
                    self.source,
                    value,  # type: ignore[arg-type]
                    False,
                    None,
                    False,
                    fake_script_obj,  # type: ignore[arg-type]
                )

            return TorchScriptObjectVariable.create(
                proxy,  # pyrefly: ignore[bad-argument-type]
                fake_script_obj,
                source=self.source,
            )
        elif (
            isinstance(value, (dict, collections.OrderedDict))
            and type(value).__new__ is dict.__new__
        ):
            # Construct a dict_vt that will reside inside the UserDefinedDictVariable
            self.install_guards(GuardBuilder.TYPE_MATCH)
            self.install_guards(GuardBuilder.SEQUENCE_LENGTH)

            # Guard on the key order
            self.tx.output.guard_on_key_order.add(self.source)

            # We need all the keys to be hashable. We do this within the
            # HashableTracker class in hashable.py
            def build_key_value(
                i: Any, k: Any, v: Any
            ) -> tuple[VariableTracker, VariableTracker]:
                base = self.get_source()
                source_key = ConstDictKeySource(base, i)
                key = LazyVariableTracker.create(k, source_key)

                source_value = DictSubclassGetItemSource(base, source_key)
                res_value = LazyVariableTracker.create(v, source_value)

                return key, res_value

            result = dict(
                build_key_value(i, k, v)
                for i, k, v in enumerate_items_with_dict_position(value)
            )

            is_ordered_dict = isinstance(value, collections.OrderedDict)
            dict_vt = ConstDictVariable(
                result,
                user_cls=(collections.OrderedDict if is_ordered_dict else dict),
                mutation_type=ValueMutationExisting(),
                source=self.source,
            )
            # Force this to reconstruct on mutation to keep the reconstruction
            # bytecode simple
            dict_vt.should_reconstruct_all = True

            if is_ordered_dict:
                result = OrderedDictVariable(value, dict_vt=dict_vt, source=self.source)
            else:
                result = UserDefinedDictVariable(
                    value, dict_vt=dict_vt, source=self.source
                )
            return self.tx.output.side_effects.track_object_existing(value, result)
        elif isinstance(value, tuple):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            self.install_guards(GuardBuilder.SEQUENCE_LENGTH)

            # NB - Be careful in not triggering user code. Guards also work on
            # the underlying tuple data structure.
            output = [
                LazyVariableTracker.create(
                    tuple.__getitem__(value, i),
                    source=GetItemSource(self.get_source(), i),
                )
                for i in range(tuple.__len__(value))
            ]

            tuple_vt = TupleVariable(
                output,  # type: ignore[arg-type]
                source=self.source,
                mutation_type=ValueMutationExisting(),
            )
            result = UserDefinedTupleVariable(
                value, tuple_vt=tuple_vt, source=self.source
            )
            return self.tx.output.side_effects.track_object_existing(value, result)
        elif isinstance(value, list):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            self.install_guards(GuardBuilder.SEQUENCE_LENGTH)

            # NB - Be careful in not triggering user code. Guards also work on
            # the underlying list data structure.
            output = [
                LazyVariableTracker.create(
                    list.__getitem__(value, i),
                    source=ListGetItemSource(self.get_source(), i),
                )
                for i in range(list.__len__(value))
            ]
            list_vt = ListVariable(
                output,  # type: ignore[arg-type]
                source=self.source,
                mutation_type=ValueMutationExisting(),
            )
            result = UserDefinedListVariable(value, list_vt=list_vt, source=self.source)
            return self.tx.output.side_effects.track_object_existing(value, result)
        elif isinstance(value, (set, frozenset)):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            self.install_guards(GuardBuilder.SEQUENCE_LENGTH)

            L = list(dict.fromkeys(value))
            output = [
                LazyVariableTracker.create(
                    list.__getitem__(L, i),
                    source=NonSerializableSetGetItemSource(self.get_source(), i),
                )
                for i in range(list.__len__(L))
            ]
            if isinstance(value, set):
                set_vt_cls = SetVariable
            else:
                assert isinstance(value, frozenset)
                set_vt_cls = FrozensetVariable

            set_vt = set_vt_cls(
                output, source=self.source, mutation_type=ValueMutationExisting()
            )
            result = UserDefinedSetVariable(value, set_vt=set_vt, source=self.source)
            return self.tx.output.side_effects.track_object_existing(value, result)
        elif issubclass(type(value), MutableMapping):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            result = MutableMappingVariable(value, source=self.source)
            return self.tx.output.side_effects.track_object_existing(value, result)
        elif is_frozen_dataclass(value):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            result = FrozenDataClassVariable(value, source=self.source)
            return self.tx.output.side_effects.track_object_existing(value, result)
        elif isinstance(value, dict_keys):
            if all(ConstantVariable.is_literal(k) for k in value):
                # If the dict_keys object is passed from outside the compile region, it must either be passed along with
                # the corresponding dict object or treated as a set (when only the keys are passed into the compiled region).
                # - If it is passed along with the dict, the dict object itself is already guarded.
                # - If only the dict_keys object is passed, we add EQUALS_MATCH and SEQUENCE_LENGTH guards
                #   to ensure it remains unchanged across multiple runs.
                items = [SourcelessBuilder.create(self.tx, v) for v in value]
                install_guard(
                    self.get_source().make_guard(GuardBuilder.SEQUENCE_LENGTH),
                    self.get_source().make_guard(GuardBuilder.EQUALS_MATCH),
                )
                return DictKeySetVariable(items, source=self.source)
            else:
                unimplemented(
                    gb_type="non-const keys in dict_keys",
                    context=f"non-const keys: {[k for k in value if not ConstantVariable.is_literal(k)]}",
                    explanation="Dynamo expects dict_keys keys to be constants.",
                    hints=[
                        "Ensure your dict_keys keys are constants (e.g. int, float, strings)",
                    ],
                )
        elif IntWrapperVariable.is_matching_object(value):
            from torch.export.dynamic_shapes import _DimHintType

            if value.dynamism is None or value.dynamism.type == _DimHintType.STATIC:
                return self.wrap_symint(value.val)
            elif value.dynamism.type == _DimHintType.DYNAMIC:
                log.debug(
                    "%s marked %s via IntWrapper",
                    self.source.name,
                    DimDynamic.DYNAMIC,
                )
                return self.wrap_symint(
                    value.val,
                    dynamism=DimDynamic.DYNAMIC,
                    context=SymIntSymbolicContext(
                        constraint=RelaxedUnspecConstraint(warn_only=False)
                    ),
                )
            elif value.dynamism.type == _DimHintType.AUTO:
                log.debug(
                    "%s marked %s via IntWrapper",
                    self.source.name,
                    DimDynamic.DYNAMIC,
                )
                return self.wrap_symint(value.val, dynamism=DimDynamic.DYNAMIC)
            else:
                raise RuntimeError(f"Undefined dynamism {value.dynamism}")
        elif istype(value, object):
            self.install_guards(GuardBuilder.TYPE_MATCH)
            return ObjectVariable(value, source=self.source)
        else:
            return self.wrap_user_defined(value)