def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        # NB - Both key and value are LazyVariableTrackers in the beginning. So,
        # we have to insert guards when a dict method is accessed. For this to
        # be simple, we are conservative and overguard. We skip guard only for
        # get/__getitem__ because the key guard will be inserted by the
        # corresponding value VT. For __contains__, we add a DICT_CONTAINS
        # guard. But for all the other methods, we insert the DICT_KEYS_MATCH
        # guard to be conservative.
        from . import DictBuiltinVariable
        from .builder import SourcelessBuilder

        Hashable = HashableTracker

        if name == "__init__":
            temp_dict_vt = DictBuiltinVariable.call_custom_dict(
                tx, dict, *args, **kwargs
            )
            tx.output.side_effects.mutation(self)
            self.items.update(temp_dict_vt.items)  # type: ignore[attr-defined]
            return ConstantVariable.create(None)
        elif name == "items":
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            self.install_dict_keys_match_guard()
            if self.source:
                tx.output.guard_on_key_order.add(self.source)
            return DictItemsVariable(self)
        elif name == "keys":
            if len(args):
                raise_args_mismatch(tx, name, "0 args", f"{len(args)} args")
            self.install_dict_keys_match_guard()
            if self.source:
                tx.output.guard_on_key_order.add(self.source)
            return DictKeysVariable(self)
        elif name == "values":
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            self.install_dict_keys_match_guard()
            if self.source:
                tx.output.guard_on_key_order.add(self.source)
            if args or kwargs:
                raise_observed_exception(TypeError, tx)
            return DictValuesVariable(self)
        elif name == "copy":
            self.install_dict_keys_match_guard()
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            return self.clone(
                items=self.items.copy(), mutation_type=ValueMutationNew(), source=None
            )
        elif name == "__setitem__" and self.is_mutable():
            arg_hashable = args and is_hashable(args[0])
            if not arg_hashable:
                raise_unhashable(args[0], tx)

            self.install_dict_keys_match_guard()
            if kwargs or len(args) != 2:
                raise_args_mismatch(
                    tx,
                    name,
                    "2 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            tx.output.side_effects.mutation(self)
            self.items[Hashable(args[0])] = args[1]
            return ConstantVariable.create(None)
        elif name == "__delitem__" and self.is_mutable():
            arg_hashable = args and is_hashable(args[0])
            if arg_hashable:
                self.install_dict_keys_match_guard()
                self.should_reconstruct_all = True
                tx.output.side_effects.mutation(self)
                self.items.__delitem__(Hashable(args[0]))
                return ConstantVariable.create(None)
            else:
                return super().call_method(tx, name, args, kwargs)
        elif name == "get":
            if len(args) not in (1, 2):
                raise_args_mismatch(tx, name, "1 or 2 args", f"{len(args)} args")

            arg_hashable = args and is_hashable(args[0])
            if not arg_hashable:
                raise_unhashable(args[0], tx)

            if args[0] not in self:
                self.install_dict_contains_guard(tx, args)
                if len(args) == 1:
                    # if default is not given, return None
                    return ConstantVariable.create(None)
                return args[1]
            # Key guarding - Nothing to do.
            return self.getitem_const(tx, args[0])
        elif name == "pop" and self.is_mutable():
            if len(args) not in (1, 2):
                raise_args_mismatch(tx, name, "1 or 2 args", f"{len(args)} args")

            arg_hashable = args and is_hashable(args[0])
            if not arg_hashable:
                raise_unhashable(args[0], tx)

            if args[0] not in self:
                # missing item, return the default value. Install no DICT_CONTAINS guard.
                self.install_dict_contains_guard(tx, args)
                if len(args) == 1:
                    # if default is not given, raise KeyError
                    raise_observed_exception(KeyError, tx)
                return args[1]

            self.should_reconstruct_all = True
            tx.output.side_effects.mutation(self)
            return self.items.pop(Hashable(args[0]))
        elif name == "popitem" and self.is_mutable():
            # dict.popitem() takes no args. OrderedDict.popitem(last=) is
            # handled by OrderedDictVariable.call_method.
            if len(args):
                raise_args_mismatch(tx, name)

            if not self.items:
                raise_observed_exception(
                    KeyError,
                    tx,
                    args=[
                        "popitem(): dictionary is empty",
                    ],
                )

            k, v = self.items.popitem()
            self.should_reconstruct_all = True
            tx.output.side_effects.mutation(self)

            return variables.TupleVariable([k.vt, v])
        elif name == "clear":
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            self.should_reconstruct_all = True
            tx.output.side_effects.mutation(self)
            self.items.clear()
            return ConstantVariable.create(None)
        elif name == "update" and self.is_mutable():
            # In general, this call looks like `a.update(b, x=1, y=2, ...)`.
            # Either `b` or the kwargs is omittable, but not both.
            self.install_dict_keys_match_guard()
            has_arg = len(args) == 1
            has_kwargs = len(kwargs) > 0
            if has_arg or has_kwargs:
                tx.output.side_effects.mutation(self)
                if has_arg:
                    dict_vt: VariableTracker
                    if isinstance(args[0], ConstDictVariable):
                        # NB - Guard on all the keys of the other dict to ensure
                        # correctness.
                        args[0].install_dict_keys_match_guard()
                        dict_vt = args[0]
                    else:
                        dict_vt = DictBuiltinVariable.call_custom_dict(
                            tx, dict, args[0]
                        )
                    self.items.update(dict_vt.items)  # type: ignore[attr-defined]
                if has_kwargs:
                    # Handle kwargs
                    kwargs_hashable = {
                        Hashable(VariableTracker.build(tx, k)): v
                        for k, v in kwargs.items()
                    }
                    self.items.update(kwargs_hashable)
                return ConstantVariable.create(None)
            else:
                return super().call_method(tx, name, args, kwargs)
        elif name == "__contains__":
            if not len(args):
                raise_args_mismatch(
                    tx,
                    name,
                    "more than 1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )

            arg_hashable = args and is_hashable(args[0])
            if not arg_hashable:
                raise_unhashable(args[0], tx)

            self.install_dict_contains_guard(tx, args)
            contains = args[0] in self
            return VariableTracker.build(tx, contains)
        elif name == "setdefault" and self.is_mutable():
            if len(args) not in (1, 2):
                raise_args_mismatch(
                    tx,
                    name,
                    "1 or 2 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )

            arg_hashable = args and is_hashable(args[0])
            if not arg_hashable:
                raise_unhashable(args[0], tx)

            self.install_dict_keys_match_guard()
            if kwargs or len(args) > 2:
                raise_args_mismatch(
                    tx,
                    name,
                    "at most 2 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            value = self.maybe_getitem_const(args[0])
            if value is not None:
                return value
            else:
                if len(args) == 1:
                    x = ConstantVariable.create(None)
                else:
                    x = args[1]
                tx.output.side_effects.mutation(self)
                self.items[Hashable(args[0])] = x
                return x
        elif name == "__eq__" and istype(
            self, ConstDictVariable
        ):  # don't let Set use this function
            if len(args) != 1:
                raise_args_mismatch(tx, name, "1 args", f"{len(args)} args")

            return SourcelessBuilder.create(tx, polyfills.dict___eq__).call_function(
                tx, [self, args[0]], {}
            )
        elif name == "__ne__":
            return VariableTracker.build(
                tx,
                not self.call_method(tx, "__eq__", args, kwargs).value,  # type: ignore[attr-defined]
            )
        elif name == "__or__":
            if len(args) != 1:
                raise_args_mismatch(tx, name, "1 args", f"{len(args)} args")
            other = args[0]

            # Method resolution for binops works as follow (using __or__ as example):
            # (1) dict.__or__(dict) => dict
            # (2) dict.__or__(subclass): return NotImplemented
            # (3) Check if subclass implements __ror__ => forward the call
            # to subclass.__ror__(dict)

            # Let's not forward the call to __ror__ yet because __ror__ can be
            # implemented in C (i.e. OrderedDict subclass) which Dynamo cannot
            # trace
            # if istype(other, variables.UserDefinedDictVariable):
            #     if other.call_obj_hasattr(tx, "__ror__").value:
            #         return other.call_method(tx, "__ror__", [self], kwargs)

            # The three dict types Dynamo can handle are dict, OrderedDict and
            # defaultdict.

            # TODO(guilhermeleobas): this check should be on builtin.py::call_or_
            if isinstance(
                other,
                (
                    ConstDictVariable,
                    variables.UserDefinedDictVariable,
                ),
            ):
                # Unwrap UserDefinedDictVariable to its underlying ConstDictVariable
                if isinstance(other, variables.UserDefinedDictVariable):
                    assert other._base_vt is not None
                    assert isinstance(other._base_vt, ConstDictVariable)
                    other = other._base_vt

                # Always return the specialized dictionary, and in the case
                # both are specialized, take the first to be the type of the
                # new dictionary
                if self.user_cls is not dict:
                    user_cls = self.user_cls
                    to_cpy = self
                else:
                    user_cls = other.user_cls
                    to_cpy = other

                to_cpy.install_dict_keys_match_guard()
                new_dict_vt = to_cpy.clone(
                    items=self.items.copy(),
                    mutation_type=ValueMutationNew(),
                    source=None,
                    user_cls=user_cls,
                )

                # NB - Guard on all the keys of the other dict to ensure
                # correctness. Use `other` (already unwrapped from
                # UserDefinedDictVariable to ConstDictVariable above).
                other.install_dict_keys_match_guard()  # type: ignore[union-attr]
                new_dict_vt.items.update(other.items)  # type: ignore[union-attr]
                return new_dict_vt
            else:
                raise_observed_exception(
                    TypeError,
                    tx,
                    args=[
                        f"unsupported operand type(s) for |: '{self.python_type().__name__}'"
                        f"and '{other.python_type().__name__}'"
                    ],
                )
        elif name == "__ior__":
            self.call_method(tx, "update", args, kwargs)
            return self
        elif name == "__iter__":
            from .lists import ListIteratorVariable

            if self.source and not is_constant_source(self.source):
                tx.output.guard_on_key_order.add(self.source)
            return ListIteratorVariable(
                self.unpack_var_sequence(tx), mutation_type=ValueMutationNew()
            )
        else:
            return super().call_method(tx, name, args, kwargs)