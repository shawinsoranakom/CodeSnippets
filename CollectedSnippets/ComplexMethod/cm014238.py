def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: Iterable[Any],
        kwargs: dict[str, Any],
    ) -> VariableTracker:
        from .builder import wrap_fx_proxy

        real_obj = self.as_python_constant()
        real_obj_type = type(real_obj)
        if is_opaque_type(real_obj_type):
            member_type = get_member_type(real_obj_type, name)

            if member_type == MemberType.USE_REAL:
                if (
                    inspect.getattr_static(real_obj_type, "__getattr__", None)
                    is not None
                ):
                    unimplemented(
                        gb_type="Opaque object with custom __getattr__ not supported",
                        context=f"{real_obj_type.__name__} with custom __getattr__",
                        explanation="Dynamo does not support opaque objects types with custom __getattr__ methods",
                        hints=[],
                    )

                args_const = [x.as_python_constant() for x in args]
                kwargs_const = {k: v.as_python_constant() for k, v in kwargs.items()}

                method = getattr(real_obj, name)

                if name == "__setattr__":
                    method(*args_const, **kwargs_const)
                    return real_obj  # pyrefly: ignore[bad-return]

                constant_val = method(*args_const, **kwargs_const)

                if any(
                    is_opaque_reference_type(type(r))
                    for r in pytree.tree_leaves(constant_val)
                ):
                    unimplemented(
                        gb_type="Opaque object member with method-type USE_REAL returned a reference-type opaque object.",
                        context=f"Opaque object type: {real_obj_type}. Method name: '{name}'",
                        explanation=(
                            "To properly guard reference-type opaque objects, "
                            "we must lift them as inputs to the graph. In order "
                            "to do this, they must all have a source, meaning they "
                            "come from a global value or are an attribute of an input."
                        ),
                        hints=[
                            f"Register member '{name}' with MemberType.INLINED in "
                            f"register_opaque_type({real_obj_type}, members=...).",
                        ],
                    )

                return VariableTracker.build(tx, constant_val)

            elif member_type == MemberType.INLINED or is_opaque_value_type(
                real_obj_type
            ):
                proxy_args, proxy_kwargs = proxy_args_kwargs(args, kwargs)

                proxy = tx.output.create_proxy(
                    "call_method",
                    name,
                    args=(self.proxy, *proxy_args),
                    kwargs=proxy_kwargs,
                )

                return wrap_fx_proxy(tx=tx, proxy=proxy)

            else:
                unimplemented(
                    gb_type="Attempted to access unregistered member on an OpaqueObject",
                    context=f"value={real_obj}, attr={name}",
                    explanation=f"Member '{name}' is not registered for this opaque object type.",
                    hints=[
                        f"Register '{name}' with a MemberType in register_opaque_type(members=...).",
                    ],
                )

        unimplemented(
            gb_type="Weird method call on TorchScript object",
            context=f"value={self.value}, method={name}",
            explanation=(
                f"This particular method call ({name}) is not supported (e.g. calling `__setattr__`). "
                "Most method calls to TorchScript objects should be supported."
            ),
            hints=[
                "Avoid calling this method.",
            ],
        )