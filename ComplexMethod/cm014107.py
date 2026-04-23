def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from .tensor import SymNodeVariable

        if name == "__setitem__" and self.is_mutable():
            if kwargs or len(args) != 2:
                raise_args_mismatch(
                    tx,
                    name,
                    "2 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            key, value = args

            if not key.is_python_constant():
                # probably will graph-break
                super().call_method(tx, name, args, kwargs)

            tx.output.side_effects.mutation(self)
            if isinstance(key, SliceVariable):
                if not value.has_force_unpack_var_sequence(tx):
                    raise_observed_exception(
                        TypeError, tx, args=["can only assign an iterable"]
                    )

                key_as_const = key.as_python_constant()
                if key_as_const.step == 0:
                    raise_observed_exception(
                        ValueError, tx, args=["slice step cannot be zero"]
                    )

                value_unpack = value.force_unpack_var_sequence(tx)
                try:
                    self.items[key_as_const] = value_unpack
                except Exception as exc:
                    raise_observed_exception(
                        type(exc),
                        tx,
                        args=list(exc.args),
                    )
            else:
                if isinstance(key, SymNodeVariable):
                    key = key.evaluate_expr()
                else:
                    key = key.as_python_constant()

                try:
                    # pyrefly: ignore[unsupported-operation]
                    self.items[key] = value
                except (IndexError, TypeError) as e:
                    raise_observed_exception(
                        type(e), tx, args=[VariableTracker.build(tx, a) for a in e.args]
                    )
            return ConstantVariable.create(None)

        if name == "sort" and self.is_mutable():
            if len(args) != 0:
                raise_args_mismatch(tx, name, "0 args", f"{len(args)} args")
            key_fn_var = kwargs.pop("key", ConstantVariable.create(None))
            reverse = kwargs.pop(
                "reverse", ConstantVariable.create(False)
            ).as_python_constant()
            if len(kwargs) != 0:
                raise_args_mismatch(tx, name, "0 kwargs", f"{len(kwargs)} kwargs")

            if key_fn_var.is_constant_none():
                keys = self.items.copy()
            else:
                keys = [key_fn_var.call_function(tx, [x], {}) for x in self.items]

            if not all(k.is_python_constant() for k in keys):
                first_non_constant_key = None
                for k in keys:
                    if not k.is_python_constant():
                        first_non_constant_key = k
                assert first_non_constant_key is not None

                try:
                    python_type = str(first_non_constant_key.python_type())
                except NotImplementedError:
                    python_type = "unknown"

                unimplemented(
                    gb_type="sort with non-constant keys",
                    context=str(first_non_constant_key),
                    explanation=(
                        f"Cannot perform sort with non-constant key. "
                        f"First non-constant key type: {python_type}. "
                        f"Most notably, we cannot sort with Tensor or SymInt keys, but we can "
                        f"sort ints."
                    ),
                    hints=["Use something else as the key."],
                )

            try:
                tx.output.side_effects.mutation(self)
                sorted_items_with_keys = sorted(
                    (
                        (
                            x,
                            k.as_python_constant(),
                            -i if reverse else i,  # extra key to ensure stable sort
                        )
                        for i, (k, x) in enumerate(zip(keys, self.items))
                    ),
                    key=operator.itemgetter(1, 2),
                    reverse=reverse,
                )
                self.items[:] = [x for x, *_ in sorted_items_with_keys]
            except Exception as e:
                raise_observed_exception(type(e), tx, args=list(e.args))
            return ConstantVariable.create(None)

        if name == "__init__" and self.is_mutable():
            if kwargs:
                raise_args_mismatch(tx, name, "0 kwargs", f"{len(kwargs)} kwargs")
            if len(args) == 0:
                return ConstantVariable.create(None)
            elif len(args) == 1 and args[0].has_force_unpack_var_sequence(tx):
                (arg,) = args
                tx.output.side_effects.mutation(self)
                self.items[:] = arg.force_unpack_var_sequence(tx)
                return ConstantVariable.create(None)

        return super().call_method(tx, name, args, kwargs)