def method_setattr_standard(
        self,
        tx: "InstructionTranslator",
        name: VariableTracker,
        value: VariableTracker,
        directly_update_dict: bool = False,
    ) -> VariableTracker:
        name_str = ""
        try:
            name_str = name.as_python_constant()
        except NotImplementedError:
            unimplemented(
                gb_type="non-const setattr name on user-defined object",
                context=f"object={self}, name={name}, value={value}",
                explanation="Detected a call to `setattr` of a user-defined object with a non-constant name.",
                hints=["Ensure that the name is a string."],
            )
        assert tx.output.side_effects.is_attribute_mutation(self), (
            "Attempted setattr on a user-defined object that does not have "
            "an AttributeMutation mutation_type"
        )

        if (
            torch.distributed.is_available()
            and type(self.value) is torch.distributed.P2POp
            and (
                tx.output.side_effects.has_pending_mutation_of_attr(self, name_str)
                or name_str in self.value.__dict__
            )
        ):
            unimplemented(
                gb_type="P2POp mutation",
                context=f"object={self}, name={name}, value={value}",
                explanation="Dynamo does not support mutating torch.distributed.P2POp instances.",
                hints=[
                    "Construct a new torch.distributed.P2POp instead of mutating an existing one inside torch.compile.",
                ],
            )

        if name_str == "__class__":
            unimplemented(
                gb_type="__class__ assignment on user-defined object",
                context=f"object={self}, value={value}",
                explanation="Dynamo does not support reassigning __class__ on user-defined objects.",
                hints=[
                    "Move the __class__ assignment outside of the torch.compile region.",
                ],
            )

        if directly_update_dict:
            self.get_dict_vt(tx).setitem(name_str, value)
        else:
            tmp = self.try_get_descritor_and_setter_py_func(name_str)
            if tmp:
                descriptor, setter = tmp
                # Emulate
                # https://github.com/python/cpython/blob/3.11/Objects/object.c#L1371-L1452
                desc_source = None
                func_source = None
                if self.cls_source:
                    desc_source = self.get_source_by_walking_mro(tx, name_str)
                    # use `type(...)` to ignore instance attrs.
                    func_source = AttrSource(TypeSource(desc_source), "__set__")
                desc_var = VariableTracker.build(tx, descriptor, desc_source)
                func_var = VariableTracker.build(tx, setter, func_source, realize=True)
                if isinstance(descriptor, property):
                    args = [self, value]  # property.fset(self, value)
                else:
                    args = [desc_var, self, value]  # __set__(desc, self, value)
                return func_var.call_function(tx, args, {})

            # Handle Python property descriptors whose __set__ is a C slot
            # wrapper (not a Python function), which the above check misses.
            # Mirrors the property getter handling in var_getattr.
            descriptor = inspect.getattr_static(type(self.value), name_str, None)
            if isinstance(descriptor, property) and descriptor.fset is not None:
                fset_source = None
                if self.cls_source:
                    fset_source = AttrSource(
                        self.get_source_by_walking_mro(tx, name_str), "fset"
                    )
                fset_var = VariableTracker.build(
                    tx, descriptor.fset, source=fset_source
                )
                return fset_var.call_function(tx, [self, value], {})

            # NOTE: else we assume the descriptor (if any) has a
            # side-effect-free `__set__` as far as Dynamo tracing is concerned.

        # If the code reaches here, the attribute is either:
        #  1) a slot descriptor
        #  2) a plain attribute with no descriptor
        # If the object has no __dict__, only slot descriptors (member_descriptor)
        # allow mutation. Any other attribute assignment raises AttributeError.
        if not hasattr(self.value, "__dict__"):
            descriptor = self.lookup_class_mro_attr(name_str)
            if not inspect.ismemberdescriptor(descriptor):
                error_msg = VariableTracker.build(
                    tx,
                    f"'{type(self.value).__name__}' object has no attribute '{name_str}'",
                )
                raise_observed_exception(AttributeError, tx, args=[error_msg])

        tx.output.side_effects.store_attr(self, name_str, value)
        return variables.ConstantVariable.create(None)