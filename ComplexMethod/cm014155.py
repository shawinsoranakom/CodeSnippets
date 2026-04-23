def call_isinstance(
        self,
        tx: "InstructionTranslator",
        arg: VariableTracker,
        isinstance_type_var: VariableTracker,
    ) -> VariableTracker:
        try:
            arg_type = arg.python_type()
        except NotImplementedError:
            unimplemented(
                gb_type="builtin isinstance() cannot determine type of argument",
                context=f"isinstance({arg}, {isinstance_type_var})",
                explanation=f"Dynamo doesn't have a rule to determine the type of argument {arg}",
                hints=[*graph_break_hints.DYNAMO_BUG],
            )
        isinstance_type = isinstance_type_var.as_python_constant()
        if isinstance(arg, variables.TensorVariable) and arg.dtype is not None:

            def _tensor_isinstance(
                tensor_var: VariableTracker, tensor_type: Any
            ) -> bool:
                def check_type(ty: Any) -> bool:
                    if ty not in tensortype_to_dtype:
                        example_val = arg.as_proxy().node.meta["example_value"]
                        if (
                            is_traceable_wrapper_subclass(example_val)
                            and ty is torch.nn.parameter.Parameter
                        ):
                            # N.B: we are calling isinstance directly on the example value.
                            # torch.nn.Parameter has a meta-class that overrides __isinstance__,
                            # the isinstance check here allows us to invoke that logic.
                            return isinstance(example_val, ty)
                        else:
                            return issubclass(arg.python_type(), ty)

                    dtypes = tensortype_to_dtype[ty]
                    # pyrefly: ignore [missing-attribute]
                    return arg.dtype in dtypes

                if type(tensor_type) is tuple:
                    return any(check_type(ty) for ty in tensor_type)
                else:
                    return check_type(tensor_type)

            return VariableTracker.build(tx, _tensor_isinstance(arg, isinstance_type))
        # UserDefinedObject with C extensions can have torch.Tensor attributes,
        # so break graph.
        if isinstance(arg, variables.UserDefinedObjectVariable) and isinstance(
            arg.value, types.MemberDescriptorType
        ):
            unimplemented(
                gb_type="isinstance() called on user defined object with C extensions",
                context=f"isinstance({arg}, {isinstance_type})",
                explanation="User-defined object with C extensions can have torch.Tensor "
                "attributes; intentionally graph breaking.",
                hints=[*graph_break_hints.SUPPORTABLE],
            )
        # handle __instancecheck__ defined in user class
        if (
            isinstance(arg, variables.UserDefinedObjectVariable)
            and "__instancecheck__" in isinstance_type.__class__.__dict__
        ):
            return VariableTracker.build(
                tx,
                isinstance_type.__class__.__instancecheck__(isinstance_type, arg.value),
            )

        if isinstance(arg, variables.UserDefinedExceptionClassVariable):
            # pyrefly: ignore [unbound-name]
            return VariableTracker.build(tx, isinstance(arg_type, isinstance_type))

        isinstance_type_tuple: tuple[type, ...]
        if isinstance(isinstance_type, type) or callable(
            # E.g. isinstance(obj, typing.Sequence)
            getattr(isinstance_type, "__instancecheck__", None)
        ):
            isinstance_type_tuple = (isinstance_type,)
        elif isinstance(isinstance_type, types.UnionType):
            isinstance_type_tuple = isinstance_type.__args__
        elif isinstance(isinstance_type, tuple) and all(
            isinstance(tp, type) or callable(getattr(tp, "__instancecheck__", None))
            for tp in isinstance_type
        ):
            isinstance_type_tuple = isinstance_type
        else:
            raise_observed_exception(
                TypeError,
                tx,
                args=[
                    "isinstance() arg 2 must be a type, a tuple of types, or a union"
                ],
            )

        try:
            # NB: `isinstance()` does not call `__subclasscheck__` but use `__instancecheck__`.
            # But usually `isinstance(obj, type_info)` and `issubclass(type(obj), type_info)` gives
            # the same result.
            # WARNING: This might run arbitrary user code `__subclasscheck__` and we did not trace
            # through it. This is a limitation of the current implementation.
            # Usually `__subclasscheck__` and `__instancecheck__` can be constant fold through, it
            # might not be a big issue and we trade off it for performance.
            val = issubclass(arg_type, isinstance_type_tuple)
        except TypeError:
            val = arg_type in isinstance_type_tuple
        return VariableTracker.build(tx, val)