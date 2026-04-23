def var_getattr(self, tx: "InstructionTranslator", name: str) -> VariableTracker:
        obj = None
        try:
            obj = inspect.getattr_static(self.value, name)
        except AttributeError:
            unimplemented(
                gb_type="Attribute not found on opaque class",
                context=f"class={self.value}, attr={name}",
                explanation=f"The attribute '{name}' does not exist on opaque class {self.value}.",
                hints=[
                    f"Ensure '{name}' is a valid attribute of {type(self.value)}.",
                ],
            )

        if isinstance(obj, staticmethod):
            obj = obj.__get__(self.value)
        elif isinstance(obj, property):
            obj = obj.__get__(None, self.value)  # pyrefly: ignore[no-matching-overload]
        elif hasattr(obj, "__get__"):
            if not isinstance(type(obj).__dict__.get("__get__"), types.FunctionType):
                # C-level descriptors are safe to resolve dynamically.
                obj = getattr(self.value, name)
            else:
                type_name = type(obj).__name__
                unimplemented(
                    gb_type="Unsupported descriptor on opaque class",
                    context=f"class={self.value}, attr={name}, descriptor={type_name}",
                    explanation=f"The attribute '{name}' is a descriptor of type '{type_name}' which is not supported.",
                    hints=[
                        "Only staticmethod, property, and pybind11_static_property are supported.",
                        "Consider accessing this attribute outside of the compiled region.",
                    ],
                )

        if ConstantVariable.is_literal(obj):
            return VariableTracker.build(tx, obj)

        source = AttrSource(self.source, name) if self.source else None
        return VariableTracker.build(tx, obj, source)