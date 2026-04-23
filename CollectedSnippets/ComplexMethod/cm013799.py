def match_schemas(cls, t: _ExtraFields_TorchOp) -> tuple[FunctionSchema, ...]:
        signature = tuple(
            # Tensor
            TensorKey.from_tensor(i)
            if isinstance(i, _TensorMetadata)
            #
            # TensorList
            else [TensorKey.from_tensor(j) for j in i]
            if isinstance(i, list)
            #
            # Scalar and uncaptured inputs.
            else i
            for i in t.inputs
        )

        def matches(schema) -> bool:
            return len(schema.arguments) == len(signature) and all(
                cls._types_match(observed, schema_arg.type)
                for observed, schema_arg in zip(
                    signature, schema.arguments, strict=True
                )
            )

        return tuple(s for s in cls.lookup_schemas(t.name) or () if matches(s))