def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from .builder import SourcelessBuilder

        if name == "__contains__":
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            return iter_contains(self.unpack_var_sequence(tx), args[0], tx)
        elif name == "index":
            if not len(args):
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )

            try:
                # Speedup trace times for constant data structures
                items = [item.as_python_constant() for item in self.items]
                const_args = [arg.as_python_constant() for arg in args]
                const_kwargs = {k: v.as_python_constant() for k, v in kwargs.items()}
                try:
                    return VariableTracker.build(
                        tx, items.index(*const_args, **const_kwargs)
                    )
                except ValueError:
                    raise_observed_exception(
                        ValueError,
                        tx,
                        args=["tuple.index()"],
                    )
            except AsPythonConstantNotImplementedError:
                return tx.inline_user_function_return(
                    VariableTracker.build(tx, polyfills.index),
                    [self] + list(args),
                    kwargs,
                )
        elif name == "count":
            if len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            return VariableTracker.build(tx, operator.countOf).call_function(
                tx,
                [self, args[0]],
                kwargs,
            )
        elif name in ("__add__", "__iadd__"):
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )

            if type(self) is not type(args[0]):
                tp_name = self.python_type_name()
                other = args[0].python_type_name()
                raise_observed_exception(
                    TypeError,
                    tx,
                    args=[
                        f'can only concatenate {tp_name} (not "{other}") to {tp_name}'
                    ],
                )

            if name == "__add__":
                return type(self)(self.items + args[0].items, source=self.source)  # type: ignore[attr-defined]
            else:
                self.items += args[0].items  # type: ignore[attr-defined]
                return self
        elif name in ("__mul__", "__imul__"):
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )

            if not (args[0].is_python_constant() and args[0].python_type() is int):
                raise_observed_exception(
                    TypeError,
                    tx,
                    args=[
                        f"can't multiply sequence by non-int type of '{args[0].python_type_name()}'"
                    ],
                )

            val = args[0].as_python_constant()

            if name == "__mul__":
                return type(self)(self.items * val, source=self.source)
            else:
                self.items *= val
                return self
        elif name in cmp_name_to_op_mapping:
            if len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )

            left = self
            right = args[0]
            # TODO this type check logic mirrors the following
            # https://github.com/python/cpython/blob/a1c52d1265c65bcf0d9edf87e143843ad54f9b8f/Objects/object.c#L991-L1007
            # But we should probably move it up the stack to so that we don't
            # need to duplicate it for different VTs.
            if not isinstance(left, BaseListVariable) or not isinstance(
                right, BaseListVariable
            ):
                if name == "__eq__":
                    return SourcelessBuilder.create(tx, operator.is_).call_function(
                        tx, (left, right), {}
                    )
                elif name == "__ne__":
                    return SourcelessBuilder.create(tx, operator.is_not).call_function(
                        tx, (left, right), {}
                    )
                else:
                    op_str = cmp_name_to_op_str_mapping[name]
                    left_ty = left.python_type_name()
                    right_ty = right.python_type_name()
                    raise_observed_exception(
                        TypeError,
                        tx,
                        args=[
                            f"{op_str} not supported between instances of '{left_ty}' and '{right_ty}'"
                        ],
                    )

            return SourcelessBuilder.create(tx, polyfills.list_cmp).call_function(
                tx,
                [
                    SourcelessBuilder.create(tx, cmp_name_to_op_mapping[name]),
                    left,
                    right,
                ],
                {},
            )
        elif name == "__iter__":
            return ListIteratorVariable(self.items, mutation_type=ValueMutationNew())

        return super().call_method(tx, name, args, kwargs)