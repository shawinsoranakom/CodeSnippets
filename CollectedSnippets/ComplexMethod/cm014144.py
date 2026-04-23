def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        # TODO(guilhermeleobas): This should actually check if args[0]
        # implements the mapping protocol.
        if name == "__eq__":
            if len(args) != 1:
                raise_args_mismatch(tx, name, "1 args", f"{len(args)} args")
            if isinstance(args[0], DictItemsVariable):
                return self.dv_dict.call_method(tx, "__eq__", [args[0].dv_dict], {})
            elif isinstance(
                args[0],
                (
                    SetVariable,
                    variables.UserDefinedSetVariable,
                    DictItemsVariable,
                    DictKeysVariable,
                ),
            ):
                return VariableTracker.build(
                    tx,
                    len(self.set_items ^ args[0].set_items) == 0,
                )
            return ConstantVariable.create(False)
        elif name == "__iter__":
            from .lists import ListIteratorVariable

            return ListIteratorVariable(
                self.view_items_vt, mutation_type=ValueMutationNew()
            )
        elif name in (
            "__and__",
            "__iand__",
            "__or__",
            "__ior__",
            "__sub__",
            "__isub__",
            "__xor__",
            "__ixor__",
        ):
            # These methods always returns a set
            fn_hdl = getattr(self.set_items, name)
            ret_val = fn_hdl(args[0].set_items)  # type: ignore[attr-defined]
            return SetVariable(ret_val)
        elif name in cmp_name_to_op_mapping:
            if not isinstance(
                args[0],
                (
                    SetVariable,
                    variables.UserDefinedSetVariable,
                    DictItemsVariable,
                    DictKeysVariable,
                ),
            ):
                return VariableTracker.build(tx, NotImplemented)
            return VariableTracker.build(
                tx,
                cmp_name_to_op_mapping[name](self.set_items, args[0].set_items),  # type: ignore[attr-defined]
            )
        return super().call_method(tx, name, args, kwargs)