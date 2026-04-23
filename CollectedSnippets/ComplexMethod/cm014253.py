def call_method(
        self,
        tx: InstructionTranslator,
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from .tensor import SymNodeVariable

        if name == "format" and istype(self.value, str):
            return variables.BuiltinVariable(str.format).call_function(
                tx, [self, *args], kwargs
            )
        elif name == "join" and istype(self.value, str):
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            arg_unpacked = args[0].force_unpack_var_sequence(tx)
            try:
                arg_const = [x.as_python_constant() for x in arg_unpacked]
                return ConstantVariable.create(self.value.join(arg_const))
            except NotImplementedError:
                return super().call_method(tx, name, args, kwargs)
        elif name == "__iter__" and istype(self.value, str):
            # this could be some generic iterator to avoid the circular import,
            # but ListIterator does what we want
            from .lists import ListIteratorVariable

            return ListIteratorVariable(
                self.unpack_var_sequence(tx), mutation_type=ValueMutationNew()
            )

        if any(isinstance(x, SymNodeVariable) for x in args):
            # Promote to SymNodeVariable for operations involving dynamic shapes.
            return variables.SymNodeVariable.create(
                tx, self.as_proxy(), self.value
            ).call_method(tx, name, args, kwargs)

        try:
            const_args = [a.as_python_constant() for a in args]
            const_kwargs = {k: v.as_python_constant() for k, v in kwargs.items()}
        except NotImplementedError:
            return super().call_method(tx, name, args, kwargs)

        if isinstance(self.value, str) and name in str.__dict__:
            method = getattr(self.value, name)
            try:
                return ConstantVariable.create(method(*const_args, **const_kwargs))
            except Exception as e:
                raise_observed_exception(type(e), tx)
        elif isinstance(self.value, (float, int)) and hasattr(self.value, name):
            if not (args or kwargs):
                try:
                    return ConstantVariable.create(getattr(self.value, name)())
                except (OverflowError, ValueError) as exc:
                    raise_observed_exception(
                        type(exc),
                        tx,
                        args=list(exc.args),
                    )
            if (
                hasattr(operator, name)
                and len(args) == 1
                and args[0].is_python_constant()
            ):
                add_target = const_args[0]
                op = getattr(operator, name)
                if isinstance(
                    add_target, (torch.SymBool, torch.SymFloat, torch.SymInt)
                ):
                    # Addition between a non sym and sym makes a sym
                    proxy = tx.output.create_proxy(
                        "call_function", op, (self.value, add_target), {}
                    )
                    return SymNodeVariable.create(tx, proxy, add_target)
                else:
                    try:
                        return ConstantVariable.create(op(self.value, add_target))
                    except Exception as e:
                        raise_observed_exception(type(e), tx, args=list(e.args))
        elif isinstance(self.value, bytes) and name == "decode":
            method = getattr(self.value, name)
            return ConstantVariable.create(method(*const_args, **const_kwargs))
        elif type(self.value) is complex and name in complex.__dict__:
            method = getattr(self.value, name)
            try:
                return ConstantVariable.create(method(*const_args, **const_kwargs))
            except Exception as e:
                raise_observed_exception(type(e), tx)

        if name == "__round__" and len(args) == 1 and args[0].is_python_constant():
            try:
                return ConstantVariable.create(
                    round(self.value, args[0].as_python_constant())
                )
            except Exception as e:
                raise_observed_exception(type(e), tx, args=list(e.args))
        elif name == "__contains__" and len(args) == 1 and args[0].is_python_constant():
            assert not kwargs
            search = args[0].as_python_constant()
            try:
                result = search in self.value
                return ConstantVariable.create(result)
            except TypeError as e:
                raise_observed_exception(type(e), tx, args=list(e.args))
        return super().call_method(tx, name, args, kwargs)