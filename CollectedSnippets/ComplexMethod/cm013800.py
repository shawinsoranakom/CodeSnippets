def _types_match(cls, observed, schema_type) -> bool:
        if isinstance(schema_type, torch._C.OptionalType):
            schema_type = schema_type.getElementType()
            return observed is None or cls._types_match(observed, schema_type)

        if isinstance(schema_type, torch._C.AnyType):
            return True

        if schema_type.isSubtypeOf(torch._C.ListType.ofTensors()):
            return isinstance(observed, list) and all(
                isinstance(i, TensorKey) for i in observed
            )

        type_map: tuple[tuple[Any, type | tuple[type, ...]], ...] = (
            (torch._C.TensorType, TensorKey),
            (torch._C.NoneType, type(None)),
            (torch._C.BoolType, bool),
            (torch._C.IntType, int),
            (torch._C.FloatType, float),
            (torch._C.ComplexType, complex),
            (torch._C.NumberType, (bool, int, float, complex)),
        )

        for jit_type, py_types in type_map:
            if isinstance(schema_type, jit_type):
                return isinstance(observed, py_types)

        # Profiler only records a subset of possible argument types. If we
        # reach this point then the schema must call for a type that profiler
        # does not record. Thus, the schema can only be a match if `observed`
        # is also None.
        return observed is None