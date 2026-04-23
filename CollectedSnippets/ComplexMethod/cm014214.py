def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from ..utils import check_constant_args
        from .builder import SourcelessBuilder

        if (
            name
            in (
                "isdisjoint",
                "union",
                "intersection",
                "difference",
                "symmetric_difference",
            )
            and check_constant_args(args, kwargs)
            and self.python_type() is set
        ):
            py_type = self.python_type()
            return self._fast_set_method(tx, getattr(py_type, name), args, kwargs)

        # Lazy imports to avoid circular dependencies
        from .dicts import DictItemsVariable, DictKeysVariable

        if name == "__init__":
            temp_set_vt = SourcelessBuilder.create(tx, set).call_set(
                tx, *args, **kwargs
            )
            tx.output.side_effects.mutation(self)
            self.items.clear()
            self.items.update(temp_set_vt.items)  # type: ignore[attr-defined]
            return ConstantVariable.create(None)
        elif name == "add":
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            # Convert add to __setitem__ with None value
            if not is_hashable(args[0]):
                raise_unhashable(args[0], tx)
            tx.output.side_effects.mutation(self)
            self.items[HashableTracker(args[0])] = SetVariable._default_value()
            return ConstantVariable.create(None)
        elif name == "pop":
            if kwargs or args:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            # Choose an item at random and pop it
            try:
                result: VariableTracker = self.set_items.pop().vt  # type: ignore[assignment]
            except KeyError as e:
                raise_observed_exception(KeyError, tx, args=list(e.args))
            self.should_reconstruct_all = True
            tx.output.side_effects.mutation(self)
            self.items.pop(HashableTracker(result))
            return result
        elif name == "isdisjoint":
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            return SourcelessBuilder.create(tx, polyfills.set_isdisjoint).call_function(
                tx, [self, args[0]], {}
            )
        elif name == "intersection":
            if kwargs:
                raise_args_mismatch(tx, name, "0 kwargs", f"{len(kwargs)} kwargs")
            return SourcelessBuilder.create(
                tx, polyfills.set_intersection
            ).call_function(
                tx,
                [self, *args],
                {"cls": self.python_type_var()},
            )
        elif name == "intersection_update":
            if kwargs:
                raise_args_mismatch(tx, name, "0 kwargs", f"{len(kwargs)} kwargs")
            return SourcelessBuilder.create(
                tx, polyfills.set_intersection_update
            ).call_function(tx, [self, *args], {})
        elif name == "union":
            if kwargs:
                raise_args_mismatch(tx, name, "0 kwargs", f"{len(kwargs)} kwargs")
            return SourcelessBuilder.create(tx, polyfills.set_union).call_function(
                tx,
                [self, *args],
                {"cls": self.python_type_var()},
            )
        elif name == "difference":
            if kwargs:
                raise_args_mismatch(
                    tx, name, f"Expect: 0 kwargs, Actual: {len(kwargs)} kwargs"
                )
            return SourcelessBuilder.create(tx, polyfills.set_difference).call_function(
                tx,
                [self, *args],
                {"cls": self.python_type_var()},
            )
        elif name == "difference_update":
            if kwargs:
                raise_args_mismatch(tx, name, "0 kwargs", f"{len(kwargs)} kwargs")
            return SourcelessBuilder.create(
                tx, polyfills.set_difference_update
            ).call_function(tx, [self, *args], {})
        elif name == "symmetric_difference":
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            return SourcelessBuilder.create(
                tx, polyfills.set_symmetric_difference
            ).call_function(
                tx,
                [self, *args],
                {"cls": self.python_type_var()},
            )
        elif name == "symmetric_difference_update":
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            return SourcelessBuilder.create(
                tx, polyfills.set_symmetric_difference_update
            ).call_function(tx, [self, *args], {})
        elif name == "update" and self.is_mutable():
            if kwargs:
                raise_args_mismatch(tx, name, "0 kwargs", f"{len(kwargs)} kwargs")
            return SourcelessBuilder.create(tx, polyfills.set_update).call_function(
                tx, [self, *args], {}
            )
        elif name == "remove":
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            if args[0] not in self:
                raise_observed_exception(KeyError, tx, args=args)
            self.should_reconstruct_all = True
            tx.output.side_effects.mutation(self)
            self.items.pop(HashableTracker(args[0]))
            return ConstantVariable.create(None)
        elif name == "discard":
            if kwargs or len(args) != 1:
                raise_args_mismatch(
                    tx,
                    name,
                    "1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            if args[0] in self:
                self.should_reconstruct_all = True
                tx.output.side_effects.mutation(self)
                self.items.pop(HashableTracker(args[0]))
            return ConstantVariable.create(None)
        elif name in ("issubset", "issuperset"):
            if len(args) != 1:
                raise_args_mismatch(tx, name, "1 args", f"{len(args)} args")

            op = {
                "issubset": operator.le,
                "issuperset": operator.ge,
            }
            other = args[0].realize()
            if not istype(other, SetVariable):
                other = SourcelessBuilder.create(tx, set).call_function(tx, [other], {})
            return SourcelessBuilder.create(tx, op.get(name)).call_function(
                tx, [self, other], {}
            )
        elif name in ("__and__", "__or__", "__xor__", "__sub__"):
            m = {
                "__and__": "intersection",
                "__or__": "union",
                "__xor__": "symmetric_difference",
                "__sub__": "difference",
            }.get(name)
            if not isinstance(
                args[0],
                (
                    SetVariable,
                    variables.UserDefinedSetVariable,
                    DictItemsVariable,
                    DictKeysVariable,
                ),
            ):
                raise_observed_exception(
                    TypeError,
                    tx,
                    args=[
                        f"unsupported operand type(s) for {name}: '{self.python_type_name()}' and '{args[0].python_type_name()}'"
                    ],
                )
            assert m is not None
            return self.call_method(tx, m, args, kwargs)
        elif name in ("__rand__", "__ror__", "__rxor__", "__rsub__"):
            m = {
                "__rand__": "__and__",
                "__ror__": "__or__",
                "__rxor__": "__xor__",
                "__rsub__": "__sub__",
            }.get(name)
            if not isinstance(
                args[0],
                (
                    SetVariable,
                    variables.UserDefinedSetVariable,
                    DictItemsVariable,
                    DictKeysVariable,
                ),
            ):
                raise_observed_exception(
                    TypeError,
                    tx,
                    args=[
                        f"unsupported operand type(s) for {name}: '{args[0].python_type_name()}' and '{self.python_type_name()}'"
                    ],
                )
            assert m is not None
            return args[0].call_method(tx, m, [self], kwargs)
        elif name in ("__iand__", "__ior__", "__ixor__", "__isub__"):
            if not isinstance(
                args[0],
                (
                    SetVariable,
                    variables.UserDefinedSetVariable,
                    DictItemsVariable,
                    DictKeysVariable,
                ),
            ):
                raise_observed_exception(
                    TypeError,
                    tx,
                    args=[
                        f"unsupported operand type(s) for {name}: '{self.python_type_name()}' and '{args[0].python_type_name()}'"
                    ],
                )
            m = {
                "__iand__": "intersection_update",
                "__ior__": "update",
                "__ixor__": "symmetric_difference_update",
                "__isub__": "difference_update",
            }.get(name)
            assert m is not None
            self.call_method(tx, m, args, kwargs)
            return self
        elif name == "__eq__":
            if not isinstance(
                args[0],
                (
                    SetVariable,
                    variables.UserDefinedSetVariable,
                    DictItemsVariable,
                    DictKeysVariable,
                ),
            ):
                return ConstantVariable.create(False)
            r = self.call_method(tx, "symmetric_difference", args, kwargs)
            return VariableTracker.build(tx, len(r.set_items) == 0)  # type: ignore[attr-defined]
        elif name == "__ne__":
            eq_result = self.call_method(tx, "__eq__", args, kwargs)
            return VariableTracker.build(tx, not eq_result.value)  # type: ignore[attr-defined]
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
        elif name == "__contains__":
            if not len(args):
                raise_args_mismatch(
                    tx,
                    name,
                    "more than 1 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            if not (args and is_hashable(args[0])):
                raise_unhashable(args[0], tx)
            self.install_set_contains_guard(tx, args)
            contains = args[0] in self
            return VariableTracker.build(tx, contains)
        elif name == "__len__":
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            return VariableTracker.build(tx, len(self.items))
        elif name == "copy":
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
        elif name == "__iter__":
            from .lists import ListIteratorVariable

            if self.source and not is_constant_source(self.source):
                tx.output.guard_on_key_order.add(self.source)
            return ListIteratorVariable(
                self.unpack_var_sequence(tx), mutation_type=ValueMutationNew()
            )
        return super().call_method(tx, name, args, kwargs)