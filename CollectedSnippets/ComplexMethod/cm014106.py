def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from .tensor import SymNodeVariable

        if name == "append" and self.is_mutable():
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            (arg,) = args
            tx.output.side_effects.mutation(self)
            self.items.append(arg)
            return ConstantVariable.create(None)
        elif name == "extend" and self.is_mutable():
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )

            if not args[0].has_force_unpack_var_sequence(tx):
                raise_observed_exception(
                    TypeError, tx, args=[f"{type(args[0])} object is not iterable"]
                )

            (arg,) = args
            arg.force_apply_to_var_sequence(
                tx, lambda item: self.call_method(tx, "append", [item], {})
            )
            return ConstantVariable.create(None)
        elif name == "insert" and self.is_mutable():
            if kwargs or len(args) != 2:
                raise_args_mismatch(
                    tx,
                    name,
                    "2 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            idx, value = args
            if isinstance(idx, SymNodeVariable):
                const_idx = idx.evaluate_expr()
            else:
                const_idx = idx.as_python_constant()
            tx.output.side_effects.mutation(self)
            # type: ignore[arg-type]
            self.items.insert(const_idx, value)
            return ConstantVariable.create(None)
        elif name == "pop" and self.is_mutable():
            if kwargs or len(args) > 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "at most 1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )

            if len(self.items) == 0:
                raise_observed_exception(IndexError, tx, args=["pop from empty list"])

            if len(args):
                idx = args[0].as_python_constant()
                if idx >= len(self.items):
                    raise_observed_exception(
                        IndexError, tx, args=["pop index out of range"]
                    )
            tx.output.side_effects.mutation(self)
            return self.items.pop(*[a.as_python_constant() for a in args])
        elif name == "clear" and self.is_mutable():
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            tx.output.side_effects.mutation(self)
            self.items.clear()
            return ConstantVariable.create(None)
        elif name == "__setitem__" and self.is_mutable() and args:
            # Realize args[0] to get the concrete type for proper type checking
            key = args[0].realize()
            if not (
                key.is_python_constant()
                or isinstance(key, SymNodeVariable)
                or (
                    isinstance(key, SliceVariable)
                    and all(
                        s.is_python_constant() or isinstance(s, SymNodeVariable)
                        for s in key.items
                    )
                )
            ):
                return super().call_method(tx, name, args, kwargs)
            if kwargs:
                raise_args_mismatch(tx, name, "0 kwargs", f"{len(kwargs)} kwargs")
            value = args[1]
            tx.output.side_effects.mutation(self)
            if isinstance(key, SymNodeVariable):
                # pyrefly: ignore[unsupported-operation]
                self.items[key.evaluate_expr()] = value
            elif isinstance(key, SliceVariable):
                if key.is_python_constant():
                    self.items[key.as_python_constant()] = list(value.items)  # type: ignore[attr-defined]
                else:
                    items_slice = slice(
                        *[
                            (
                                s.evaluate_expr()
                                if isinstance(s, SymNodeVariable)
                                else s.as_python_constant()
                            )
                            for s in key.items
                        ]
                    )
                    self.items[items_slice] = list(value.items)  # type: ignore[attr-defined]
            else:
                self.items[key.as_python_constant()] = value
            return ConstantVariable.create(None)
        elif name == "__delitem__" and self.is_mutable():
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )

            tx.output.side_effects.mutation(self)
            if args[0].is_python_constant() and isinstance(
                args[0].as_python_constant(), (int, slice)
            ):
                if isinstance(args[0], SymNodeVariable):
                    idx = args[0].evaluate_expr()
                else:
                    idx = args[0].as_python_constant()

                try:
                    self.items.__delitem__(idx)  # type: ignore[arg-type]

                except (IndexError, ValueError) as exc:
                    raise_observed_exception(
                        type(exc),
                        tx,
                        args=list(exc.args),
                    )
            else:
                msg = f"list indices must be integers or slices, not {args[0].python_type_name()}"
                raise_type_error(tx, msg)
            return ConstantVariable.create(None)
        elif name == "copy":
            # List copy() doesn't have args and kwargs
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            items_lst: list[VariableTracker] = list(self.items)
            return self.modified(items_lst, mutation_type=ValueMutationNew())
        elif name == "reverse" and self.is_mutable():
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            self.items.reverse()
            tx.output.side_effects.mutation(self)
            return ConstantVariable.create(None)
        elif name == "remove" and self.is_mutable():
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )

            idx = self.call_method(tx, "index", args, kwargs)
            self.call_method(tx, "pop", [idx], {})
            return ConstantVariable.create(None)
        else:
            return super().call_method(tx, name, args, kwargs)