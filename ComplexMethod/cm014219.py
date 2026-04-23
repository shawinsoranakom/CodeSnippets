def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from .builder import SourcelessBuilder

        if (
            name == "__subclasses__"
            and len(args) == 0
            and not kwargs
            and "__subclasses__" not in self.value.__dict__
        ):
            source = self.source
            if self.source:
                source = AttrSource(self.source, "__subclasses__")
                source = CallFunctionNoArgsSource(source)
            return VariableTracker.build(tx, self.value.__subclasses__(), source)
        elif (
            self.value in {collections.OrderedDict, collections.defaultdict}
            and name == "fromkeys"
        ):
            return variables.DictBuiltinVariable.call_custom_dict_fromkeys(
                tx, self.value, *args, **kwargs
            )
        elif self.value is collections.OrderedDict and name == "move_to_end":
            return args[0].call_method(tx, name, [*args[1:]], kwargs)
        elif name == "__len__" and len(args) == 1 and not kwargs:
            from .object_protocol import generic_len

            return generic_len(tx, args[0])
        elif name == "__eq__" and len(args) == 1 and hasattr(args[0], "value"):
            return VariableTracker.build(tx, self.value == args[0].value)
        elif name == "__ne__" and len(args) == 1 and hasattr(args[0], "value"):
            return VariableTracker.build(tx, self.value != args[0].value)
        elif issubclass(self.value, dict) and name != "__new__":
            # __new__ is handled below
            return SourcelessBuilder.create(tx, dict).call_method(
                tx, name, args, kwargs
            )
        elif issubclass(self.value, (set, frozenset)) and name != "__new__":
            # __new__ is handled below
            return SourcelessBuilder.create(tx, set).call_method(tx, name, args, kwargs)
        elif (
            len(args) == 1
            and isinstance(args[0], variables.GenericContextWrappingVariable)
            and name == "__enter__"
        ):
            return args[0].enter(tx)
        elif name == "__new__" and UserDefinedClassVariable.is_supported_new_method(
            self.value.__new__
        ):
            # Some C-level tp_new functions (dict.__new__, set.__new__) ignore
            # extra args — only the type arg matters.  Pass init_args=[] for
            # those so reconstruction emits base_cls.__new__(cls) without
            # unreconstructable args (e.g. generators).  Other tp_new functions
            # (tuple.__new__, BaseException.__new__) use the extra args.
            new_fn = self.value.__new__
            if new_fn in (dict.__new__, set.__new__):
                init_args: list[VariableTracker] = []
            else:
                init_args = list(args[1:])
            return tx.output.side_effects.track_new_user_defined_object(
                self,
                args[0],
                init_args,
            )
        elif name == "__setattr__" and self.ban_mutation:
            unimplemented(
                gb_type="Class attribute mutation when the __dict__ was already materialized",
                context=str(self.value),
                explanation="Dyanmo does not support tracing mutations on a class when its __dict__ is materialized",
                hints=graph_break_hints.SUPPORTABLE,
            )

        # Dispatch dunder methods defined on the metaclass (e.g., EnumType.__contains__).
        # In Python, `x in Color` calls `type(Color).__contains__(Color, x)`.
        metaclass = type(self.value)
        if metaclass is not type:
            # Look up the method on the metaclass MRO, not the class MRO
            for klass in metaclass.__mro__:
                if name in klass.__dict__:
                    method = klass.__dict__[name]
                    if isinstance(method, types.FunctionType):
                        source = self.source and AttrSource(self.source, name)
                        return variables.UserMethodVariable(
                            method, self, source=source
                        ).call_function(tx, args, kwargs)
                    break

        return super().call_method(tx, name, args, kwargs)