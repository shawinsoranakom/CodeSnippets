def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if (
            name == "__setitem__"
            and self.is_mutable()
            and args
            and args[0].is_python_constant()
        ):
            if kwargs or len(args) != 2:
                raise_args_mismatch(
                    tx,
                    name,
                    "2 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            key, value = args
            assert key.is_python_constant()
            assert isinstance(key.as_python_constant(), int)
            tx.output.side_effects.mutation(self)
            self.items[key.as_python_constant()] = value
            return ConstantVariable.create(None)

        maxlen = self.maxlen.as_python_constant()
        if maxlen is not None:
            slice_within_maxlen = slice(-maxlen, None)
        else:
            slice_within_maxlen = None

        if (
            name == "extendleft"
            and self.is_mutable()
            and len(args) > 0
            and args[0].has_force_unpack_var_sequence(tx)
        ):
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            # NOTE this is inefficient, but the alternative is to represent self.items
            # as a deque, which is a more intrusive change.
            args[0].force_apply_to_var_sequence(
                tx, lambda item: self.call_method(tx, "appendleft", [item], {})
            )
            slice_within_maxlen = slice(None, maxlen)
            result = ConstantVariable.create(None)
        elif name == "popleft" and self.is_mutable():
            if kwargs or len(args) > 0:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            tx.output.side_effects.mutation(self)
            result, *self.items[:] = self.items
        elif name == "appendleft" and len(args) > 0 and self.is_mutable():
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            tx.output.side_effects.mutation(self)
            self.items[:] = [args[0], *self.items]
            slice_within_maxlen = slice(None, maxlen)
            result = ConstantVariable.create(None)
        elif name == "insert" and len(args) > 0 and self.is_mutable():
            if kwargs or len(args) != 2:
                raise_args_mismatch(
                    tx,
                    name,
                    "2 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            if maxlen is not None and len(self.items) == maxlen:
                raise_observed_exception(
                    IndexError, tx, args=["deque already at its maximum size"]
                )
            result = super().call_method(tx, name, args, kwargs)
        else:
            result = super().call_method(tx, name, args, kwargs)

        if (
            slice_within_maxlen is not None
            and maxlen is not None
            and len(self.items) > maxlen
        ):
            self.items[:] = self.items[slice_within_maxlen]
        return result