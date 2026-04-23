def var_getattr(self, tx: "InstructionTranslator", name: str) -> VariableTracker:
        from torch._higher_order_ops.torchbind import call_torchbind

        from .higher_order_ops import TorchHigherOrderOperatorVariable

        real_obj = self.as_python_constant()
        real_obj_type = type(real_obj)
        if is_opaque_type(real_obj_type):
            member_type = get_member_type(real_obj_type, name)

            if member_type == MemberType.USE_REAL:
                value = getattr(real_obj, name)
                if inspect.ismethod(value) or isinstance(
                    value, types.MethodWrapperType
                ):
                    return LambdaVariable(
                        lambda *args, **kwargs: self.call_method(tx, name, args, kwargs)
                    )
                else:
                    return super().var_getattr(tx, name)

            elif member_type == MemberType.INLINED:
                value = getattr(real_obj, name)
                if (
                    inspect.ismethod(value)
                    or isinstance(value, types.MethodWrapperType)
                ) and self.source is None:
                    # When we don't have a source, fall back to call_method
                    # which creates a proxy node.
                    return LambdaVariable(
                        lambda *args, **kwargs: self.call_method(tx, name, args, kwargs)
                    )
                return super().var_getattr(tx, name)

            elif is_opaque_value_type(real_obj_type):
                return super().var_getattr(tx, name)

            elif name in ("__bool__", "__len__") and not hasattr(real_obj, name):
                # Special case: __bool__ and __len__ are used for truthiness checks.
                # If they're not registered and the real object doesn't have them,
                # raise ObservedAttributeError so the caller can fall back to
                # treating the object as truthy (Python default behavior
                raise_observed_exception(AttributeError, tx)

            else:
                unimplemented(
                    gb_type="Attempted to access unregistered member on an OpaqueObject",
                    context=f"value={real_obj}, attr={name}",
                    explanation=f"Member '{name}' is not registered for this opaque object type.",
                    hints=[
                        f"Register '{name}' with a MemberType in register_opaque_type(members=...).",
                    ],
                )

        method = getattr(self.value, name, None)
        if method is None:
            unimplemented(
                gb_type="FakeScriptObject missing method implementation",
                context=f"value={self.value}, method={name}",
                explanation=f"TorchScript object {self.value} doesn't define the method {name}.",
                hints=[
                    f"Ensure the method {name} is implemented in {self.value}.",
                    *graph_break_hints.USER_ERROR,
                ],
            )

        if not callable(method):
            unimplemented(
                gb_type="Attempted to access non-callable attribute of TorchScript object",
                context=f"value={self.value}, method={name}",
                explanation="Attribute accesses of TorchScript objects to non-callable attributes are not supported.",
                hints=[
                    "Use method calls instead of attribute access.",
                ],
            )

        assert self.source is not None
        return TorchHigherOrderOperatorVariable.make(
            call_torchbind,
            source=AttrSource(self.source, name),
            script_obj_var=self,
            method_name=name,
        )