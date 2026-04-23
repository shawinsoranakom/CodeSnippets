def _call_iter_tuple_list(
        self,
        tx: "InstructionTranslator",
        obj: VariableTracker | None = None,
        *args: VariableTracker,
        **kwargs: VariableTracker,
    ) -> VariableTracker | None:
        assert not isinstance(obj, variables.IteratorVariable)

        if self._dynamic_args(*args, **kwargs):
            return self._dyn_proxy(tx, *args, **kwargs)

        cls = variables.BaseListVariable.cls_for(self.fn)
        if obj is None:
            return cls(
                [],
                mutation_type=ValueMutationNew(),
            )
        elif obj.has_unpack_var_sequence(tx):
            if obj.source and not is_constant_source(obj.source):
                if isinstance(obj, TupleIteratorVariable):
                    install_guard(
                        obj.source.make_guard(GuardBuilder.TUPLE_ITERATOR_LEN)
                    )
                else:
                    if getattr(obj, "source", False) and isinstance(
                        obj,
                        (
                            ConstDictVariable,
                            variables.OrderedSetVariable,
                            variables.DictKeySetVariable,
                        ),
                    ):
                        tx.output.guard_on_key_order.add(obj.source)

                    if isinstance(obj, variables.MappingProxyVariable):
                        # This could be an overguarding, but its rare to iterate
                        # through a mapping proxy and not use the keys.
                        install_guard(
                            obj.source.make_guard(GuardBuilder.MAPPING_KEYS_CHECK)
                        )
                    elif not isinstance(obj, variables.UnspecializedNNModuleVariable):
                        # Prevent calling __len__ method for guards, the tracing
                        # of __iter__ will insert the right guards later.
                        install_guard(
                            obj.source.make_guard(GuardBuilder.SEQUENCE_LENGTH)
                        )

            return cls(
                list(obj.unpack_var_sequence(tx)),
                mutation_type=ValueMutationNew(),
            )
        return None