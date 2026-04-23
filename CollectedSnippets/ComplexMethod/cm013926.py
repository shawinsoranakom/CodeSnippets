def get_guard_manager_from_source(self, source: Source) -> GuardManager:
        root_guard_manager = self.guard_manager.root

        example_value = None
        source_name = source.name

        if source_name != "" and source_name in self._cached_guard_managers:
            return self._cached_guard_managers[source_name]

        if source_name != "":
            example_value = self.get(source)
            self.guard_tree_values[id(example_value)] = example_value

        guard_manager_enum = self.get_guard_manager_type(source, example_value)

        # Get base manager related information
        base_source_name = None
        base_example_value = None
        base_guard_manager = None
        base_guard_manager_enum = GuardManagerType.GUARD_MANAGER
        if isinstance(source, ChainedSource):
            base_source_name = source.base.name
            base_example_value = self.get(source.base)
            base_guard_manager = self.get_guard_manager_from_source(source.base)
            base_guard_manager_enum = self.get_guard_manager_type(
                source.base, base_example_value
            )

        # Use istype instead of isinstance to check for exact type of source.
        if istype(source, LocalSource):
            framelocals_idx = get_framelocals_idx(self.f_code, source.local_name)
            out = root_guard_manager.framelocals_manager(
                key=(source.local_name, framelocals_idx),
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, GlobalSource):
            # Global manager accepts a dict but it is not a DictGuardManager
            # because globals dict is big and we typically guard on a very
            # selected items on globals.
            out = self.get_global_guard_manager().dict_getitem_manager(
                key=source.global_name,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, GlobalWeakRefSource):
            out = self.get_global_guard_manager().global_weakref_manager(
                global_name=source.global_name,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, GlobalStateSource):
            # Don't do anything here. We guard on global state completely in
            # C++. So just return the root mgr.
            return root_guard_manager
        elif istype(source, ShapeEnvSource):
            return root_guard_manager
        elif istype(source, TypeSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.type_manager(
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, TypeDictSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.type_dict_manager(
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, TypeMROSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.type_mro_manager(
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(
            source,
            (
                OptimizerSource,
                NNModuleSource,
                UnspecializedNNModuleSource,
                UnspecializedBuiltinNNModuleSource,
                FSDPNNModuleSource,
            ),
        ):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager
        elif istype(source, ImportSource):
            module = importlib.import_module(source.module_name)
            out = root_guard_manager.lambda_manager(
                python_lambda=lambda _, m=module: m,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, TorchFunctionModeStackSource):
            out = root_guard_manager.lambda_manager(
                python_lambda=lambda _: get_torch_function_mode_stack_at(
                    source._get_index()
                ),
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, CurrentStreamSource):
            out = root_guard_manager.lambda_manager(
                python_lambda=lambda _: get_current_stream(source.device),
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, GradSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.grad_manager(
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, GenericAttrSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.generic_getattr_manager(
                attr=source.member,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(
            source, (AttrSource, CellContentsSource, UnspecializedParamBufferSource)
        ):
            assert base_guard_manager  # to make mypy happy
            assert isinstance(source, AttrSource)
            if should_optimize_getattr_on_nn_module(base_example_value):
                assert base_source_name
                out = self.getattr_on_nn_module(
                    source,
                    base_guard_manager,
                    base_example_value,
                    example_value,
                    base_source_name,
                    source_name,
                    guard_manager_enum,
                )
            else:
                out = base_guard_manager.getattr_manager(
                    attr=source.member,
                    source=source_name,
                    example_value=example_value,
                    guard_manager_enum=guard_manager_enum,
                )
        elif istype(source, (DictGetItemSource, DictSubclassGetItemSource)):
            assert base_guard_manager  # to make mypy happy
            assert isinstance(base_example_value, (dict, collections.OrderedDict))
            assert isinstance(source, (DictGetItemSource, DictSubclassGetItemSource))
            if isinstance(base_guard_manager, DictGuardManager):
                assert self.manager_guards_on_keys(base_guard_manager_enum)
                out = getitem_on_dict_manager(
                    source,
                    base_guard_manager,
                    base_example_value,
                    example_value,
                    guard_manager_enum,
                )
            else:
                if isinstance(source.index, ConstDictKeySource):
                    raise RuntimeError(
                        "Expecting clean index here. Likely Dynamo forgot to mark"
                        " a dict as guard_on_key_order"
                    )
                out = base_guard_manager.dict_getitem_manager(
                    key=source.index,
                    source=source_name,
                    example_value=example_value,
                    guard_manager_enum=guard_manager_enum,
                )
        elif istype(source, TensorPropertySource):
            out = getattr(
                base_guard_manager,
                f"tensor_property_{source.prop.name.lower()}_manager",
            )(
                idx=source.idx,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, IndexedSource):
            assert base_guard_manager  # to make mypy happy

            out = base_guard_manager.indexed_manager(
                idx=source.idx,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, ListGetItemSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.list_getitem_manager(
                key=source.index,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, GetItemSource):
            assert base_guard_manager  # to make mypy happy
            assert not isinstance(
                base_example_value, (dict, collections.OrderedDict)
            ), "Use DictGetItemSource"
            if isinstance(base_example_value, list) and not source.index_is_slice:
                out = base_guard_manager.list_getitem_manager(
                    key=source.index,
                    source=source_name,
                    example_value=example_value,
                    guard_manager_enum=guard_manager_enum,
                )
            elif isinstance(base_example_value, tuple) and not source.index_is_slice:
                out = base_guard_manager.tuple_getitem_manager(
                    key=source.index,
                    source=source_name,
                    example_value=example_value,
                    guard_manager_enum=guard_manager_enum,
                )
            else:
                index = source.index
                if source.index_is_slice:
                    index = source.unpack_slice()
                out = base_guard_manager.getitem_manager(
                    key=index,
                    source=source_name,
                    example_value=example_value,
                    guard_manager_enum=guard_manager_enum,
                )
        elif istype(source, DefaultsSource):
            assert base_guard_manager  # to make mypy happy
            assert base_source_name
            assert callable(base_example_value)
            if not source.is_kw:
                out = base_guard_manager.func_defaults_manager(
                    source=base_source_name,
                    example_value=base_example_value.__defaults__,
                    guard_manager_enum=GuardManagerType.GUARD_MANAGER,
                ).getitem_manager(
                    key=source.idx_key,
                    source=source_name,
                    example_value=example_value,
                    guard_manager_enum=guard_manager_enum,
                )
            else:
                # kwdefauts is a dict, so use a DictGuardManager
                kwdefaults = base_example_value.__kwdefaults__
                assert base_source_name is not None
                kw_source = base_source_name + ".__kwdefaults__"

                # kwdefaults is a dict. No need to guard on dict order.
                dict_mgr = base_guard_manager.func_kwdefaults_manager(
                    source=kw_source,
                    example_value=kwdefaults,
                    guard_manager_enum=GuardManagerType.GUARD_MANAGER,
                )
                assert not isinstance(dict_mgr, DictGuardManager)

                out = dict_mgr.dict_getitem_manager(
                    key=source.idx_key,
                    source=source_name,
                    example_value=example_value,
                    guard_manager_enum=guard_manager_enum,
                )
        elif istype(source, NumpyTensorSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.lambda_manager(
                python_lambda=from_numpy,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, SubclassAttrListSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.lambda_manager(
                python_lambda=lambda x: x.__tensor_flatten__()[0],
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, FlattenScriptObjectSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.lambda_manager(
                python_lambda=lambda x: x.__obj_flatten__(),
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, ScriptObjectQualifiedNameSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.lambda_manager(
                python_lambda=lambda x: x._type().qualified_name(),
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, AttrProxySource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.lambda_manager(
                python_lambda=lambda x: x.get_base(),
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, CallMethodItemSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.lambda_manager(
                python_lambda=lambda x: x.item(),
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, FloatTensorSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.lambda_manager(
                python_lambda=lambda x: torch._as_tensor_fullprec(x),
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, TupleIteratorGetItemSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.tuple_iterator_getitem_manager(
                index=source.index,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif isinstance(source, ConstDictKeySource):
            if not isinstance(base_guard_manager, DictGuardManager):
                raise AssertionError(
                    "ConstDictKeySource can only work on DictGuardManager"
                )
            out = base_guard_manager.get_key_manager(
                index=source.index,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, NonSerializableSetGetItemSource):
            assert base_guard_manager
            out = base_guard_manager.set_getitem_manager(
                index=source.index,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, WeakRefCallSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.weakref_call_manager(
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, CallFunctionNoArgsSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.call_function_no_args_manager(
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, DataclassFieldsSource):
            assert base_guard_manager
            out = base_guard_manager.lambda_manager(
                python_lambda=lambda x: dataclass_fields(x),
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, NamedTupleFieldsSource):
            assert base_guard_manager
            out = base_guard_manager.lambda_manager(
                python_lambda=lambda x: x._fields,
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, CodeSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.code_manager(
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, ClosureSource):
            assert base_guard_manager  # to make mypy happy
            out = base_guard_manager.closure_manager(
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        elif istype(source, DynamicScalarSource):
            assert base_guard_manager
            out = base_guard_manager.lambda_manager(
                python_lambda=lambda x: int(x),
                source=source_name,
                example_value=example_value,
                guard_manager_enum=guard_manager_enum,
            )
        else:
            raise AssertionError(
                f"missing guard manager builder {source} - {source.name}"
            )

        self._cached_guard_managers[source.name] = out
        return out