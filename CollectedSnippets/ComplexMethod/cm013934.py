def serialize_guards(
        self,
        builder: GuardBuilder,
        sorted_guards: list[Guard],
        output_graph: OutputGraphCommon,
    ) -> bytes:
        # We check whether our list of guards are serializable here
        for guard in sorted_guards:
            guard_type = guard.create_fn_name()
            derived_guard_types = tuple(guard.guard_types) if guard.guard_types else ()
            # BUILTIN_MATCH calls TYPE_MATCH sometimes, so we need to check both for
            # a chance that the guard is unserializable
            if guard_type in ("TYPE_MATCH", "BUILTIN_MATCH"):
                if guard._unserializable:
                    # Only call builder.get again if we know we're going to throw
                    obj = builder.get(guard)
                    raise_local_type_error(obj)
            elif (
                guard_type in CheckFunctionManager.UNSUPPORTED_SERIALIZATION_GUARD_TYPES
            ):
                raise torch._dynamo.exc.PackageError(
                    f"{guard_type} guard cannot be serialized."
                )
            elif failed := next(
                (
                    i
                    for i in derived_guard_types
                    if i in CheckFunctionManager.UNSUPPORTED_SERIALIZATION_GUARD_TYPES
                ),
                None,
            ):
                # Just raise the first failed guard name
                raise torch._dynamo.exc.PackageError(
                    f"{failed} guard cannot be serialized."
                )

        builtins_dict_name = output_graph.name_of_builtins_dict_key_in_fglobals or ""
        used_global_vars = set()
        used_local_vars = set()

        def prune_variable(source: Source) -> None:
            if name := get_global_source_name(source):
                assert isinstance(name, str)
                # Leave out the builtins dict key, as we will special handle
                # it later because the guarded code rarely use the entire
                # builtin dict in the common case.
                if name != builtins_dict_name:
                    used_global_vars.add(name)
            elif name := get_local_source_name(source):
                assert isinstance(name, str)
                used_local_vars.add(name)

        output_graph_guards_state = output_graph.dump_guards_state()
        # Only serialize the global variables that are actually used in guards.
        for guard in sorted_guards:
            if isinstance(guard.originating_source, ShapeEnvSource):
                assert self.shape_code_parts
                for source in self.shape_code_parts.shape_env_sources:
                    prune_variable(source)
            else:
                prune_variable(guard.originating_source)

        for source in output_graph.guard_on_key_order:
            prune_variable(source)

        def normalize_create_fn(x: Callable[..., None]) -> Callable[..., None]:
            if isinstance(x, functools.partial):

                def _ref(x: Any) -> Any:
                    if isinstance(x, (TensorWeakRef, weakref.ref)):
                        return x()
                    return x

                new_args = tuple(_ref(a) for a in x.args)
                new_keywords = {k: _ref(v) for k, v in x.keywords.items()}
                return functools.partial(x.func, *new_args, **new_keywords)

            return x

        global_scope_state = {
            k: v
            for k, v in output_graph_guards_state.global_scope.items()
            if k in used_global_vars or k in self.additional_used_global_vars
        }
        global_scope_state[builtins_dict_name] = {
            k: v
            # pyrefly: ignore [missing-attribute]
            for k, v in output_graph_guards_state.global_scope[
                builtins_dict_name
            ].items()  # type: ignore[attr-defined]
            if k in self.used_builtin_vars
        }
        output_graph_guards_state = dataclasses.replace(
            output_graph_guards_state,
            local_scope={
                k: v
                for k, v in output_graph_guards_state.local_scope.items()
                if k in used_local_vars or k in self.additional_used_local_vars
            },
            global_scope=global_scope_state,
            _guards=torch._guards.GuardsSet(
                OrderedSet(
                    dataclasses.replace(
                        guard,
                        obj_weakref=None,
                        guarded_class_weakref=None,
                        create_fn=normalize_create_fn(guard.create_fn),
                    )
                    for guard in sorted_guards
                )
            ),
            input_source_to_sizes_strides=pytree.tree_map(
                convert_int_to_concrete_values,
                output_graph_guards_state.input_source_to_sizes_strides,
            ),
            skip_guards_check=True,
        )
        guards_state = GuardsState(
            output_graph=output_graph_guards_state,
            shape_code_parts=self.shape_code_parts,
        )

        return pickle_guards_state(guards_state, builder)