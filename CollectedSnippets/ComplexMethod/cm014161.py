def call_custom_dict_fromkeys(
        tx: "InstructionTranslator",
        user_cls: type,
        /,
        *args: VariableTracker,
        **kwargs: VariableTracker,
    ) -> VariableTracker:
        if user_cls not in {dict, OrderedDict, defaultdict}:
            unimplemented(
                gb_type="Unsupported dict type for fromkeys()",
                context=f"{user_cls.__name__}.fromkeys(): {args} {kwargs}",
                explanation=f"Failed to call {user_cls.__name__}.fromkeys() because "
                f"{user_cls.__name__} is not any type of dict, OrderedDict, or defaultdict",
                hints=[
                    f"Ensure {user_cls.__name__} is a type of dict, OrderedDict, or defaultdict.",
                ],
            )
        if kwargs:
            # Only `OrderedDict.fromkeys` accepts `value` passed by keyword
            if (
                user_cls is not OrderedDict
                or len(args) != 1
                or len(kwargs) != 1
                or "value" not in kwargs
            ):
                raise_args_mismatch(
                    tx,
                    f"{user_cls.__name__}.fromkeys",
                    "1 args and 1 kwargs (`value`)",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            args = (*args, kwargs.pop("value"))
        if len(args) == 0:
            raise_args_mismatch(
                tx,
                f"{user_cls.__name__}.fromkeys",
                "at least 1 args",
                f"{len(args)} args",
            )
        if len(args) == 1:
            args = (*args, ConstantVariable.create(None))
        if len(args) != 2:
            raise_args_mismatch(
                tx,
                f"{user_cls.__name__}.fromkeys",
                "2 args",
                f"{len(args)} args",
            )

        arg, value = args

        def _make_result(
            items: dict[VariableTracker, VariableTracker],
        ) -> VariableTracker:
            if user_cls is OrderedDict:
                from .builder import SourcelessBuilder
                from .user_defined import OrderedDictVariable

                result = tx.output.side_effects.track_new_user_defined_object(
                    SourcelessBuilder.create(tx, dict),
                    SourcelessBuilder.create(tx, OrderedDict),
                    [],
                )
                assert isinstance(result, OrderedDictVariable)
                result._base_vt = ConstDictVariable(
                    items,
                    user_cls=OrderedDict,
                    mutation_type=ValueMutationNew(),
                )
                return result
            elif user_cls is defaultdict:
                from .builder import SourcelessBuilder
                from .user_defined import DefaultDictVariable

                result = tx.output.side_effects.track_new_user_defined_object(
                    SourcelessBuilder.create(tx, dict),
                    SourcelessBuilder.create(tx, defaultdict),
                    [],
                )
                assert isinstance(result, DefaultDictVariable)
                result._base_vt = ConstDictVariable(
                    items, mutation_type=ValueMutationNew()
                )
                return result
            else:
                return ConstDictVariable(items, mutation_type=ValueMutationNew())

        if isinstance(arg, dict):
            arg_list = [VariableTracker.build(tx, k) for k in arg]
            return _make_result(dict.fromkeys(arg_list, value))
        elif arg.has_force_unpack_var_sequence(tx):
            keys = arg.force_unpack_var_sequence(tx)
            if all(is_hashable(v) for v in keys):
                return _make_result(dict.fromkeys(keys, value))

        unimplemented(
            gb_type="failed to call dict.fromkeys()",
            context=f"{user_cls.__name__}.fromkeys(): {args} {kwargs}",
            explanation=f"Failed to call {user_cls.__name__}.fromkeys() because "
            "arguments could not be automatically converted to a list, "
            "or some dict key is not hashable.",
            hints=[
                "Manually convert the argument to a list.",
                "Ensure all keys are hashable.",
            ],
        )