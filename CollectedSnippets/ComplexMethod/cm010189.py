def serialize_inputs(
        self,
        target: Any,  # torch._ops.OpOverload and other custom operator types.
        args,
        kwargs=None,
    ) -> list[NamedArgument]:
        schema = None
        serialized_args = []

        if isinstance(target, torch._higher_order_ops.torchbind.CallTorchBind):
            obj = args[0]
            method = args[1]
            schema = target.schema(obj, method)
        else:
            if not isinstance(
                target, (torch._ops.OpOverload, *_registered_extension_types())
            ):
                raise AssertionError(
                    f"expected OpOverload or registered extension type, got {type(target).__name__}"
                )
            schema = _get_schema_from_target(target)
        if schema is None:
            raise AssertionError("schema should not be None")
        kwargs = kwargs or {}

        for i, schema_arg in enumerate(schema.arguments):
            if schema_arg.name in kwargs:
                serialized_args.append(
                    NamedArgument(
                        name=schema_arg.name,
                        arg=self.serialize_input(
                            kwargs[schema_arg.name], schema_arg.type
                        ),
                        kind=ArgumentKind.KEYWORD,
                    )
                )
            elif not schema_arg.kwarg_only and i < len(args):
                serialized_args.append(
                    NamedArgument(
                        name=schema_arg.name,
                        arg=self.serialize_input(args[i], schema_arg.type),
                        kind=ArgumentKind.POSITIONAL,
                    )
                )
            else:
                # We intentionally don't serialize the missing arguments
                # with default values
                pass

        return serialized_args