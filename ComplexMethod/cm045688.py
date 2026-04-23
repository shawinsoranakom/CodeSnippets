def denumpify(x, type_from_schema: dt.DType | None = None):
    def denumpify_inner(x):
        if pd.api.types.is_scalar(x) and pd.isna(x):
            return None
        if isinstance(x, np.generic):
            return x.item()
        return x

    def _is_instance_of_simple_type(x):
        return (
            dt.INT.is_value_compatible(x)
            or dt.BOOL.is_value_compatible(x)
            or dt.STR.is_value_compatible(x)
            or dt.BYTES.is_value_compatible(x)
            or dt.FLOAT.is_value_compatible(x)
        )

    def fix_possibly_misassigned_type(entry, type_from_schema):
        assert (
            (type_from_schema.is_value_compatible(entry))
            # the only exception for str should be conversion to bytes; however,
            # some places use schema_from_pandas, which considers some complex types
            # as str, which means we enter here, as it looks like simple type STR even
            # though it's not, below the exception that should be here
            # or (isinstance(v, str) and type_from_schema.wrapped == bytes)
            or type_from_schema.wrapped == str
        )

        if type_from_schema == dt.STR and _is_instance_of_simple_type(entry):
            return str(entry)

        if type_from_schema == dt.FLOAT:
            return float(entry)

        if isinstance(entry, str) and type_from_schema == dt.BYTES:
            return entry.encode("utf-8")

        return entry

    v = denumpify_inner(x)

    if isinstance(type_from_schema, dt._SimpleDType):
        v = fix_possibly_misassigned_type(v, type_from_schema)
    elif (
        isinstance(type_from_schema, dt.Optional)
        and isinstance(type_from_schema.wrapped, dt._SimpleDType)
        and not dt.NONE.is_value_compatible(v)
    ):
        # pandas stores optional ints as floats
        if isinstance(v, float) and type_from_schema.wrapped == dt.INT:
            assert v.is_integer()
            v = fix_possibly_misassigned_type(int(v), type_from_schema.wrapped)
        else:
            v = fix_possibly_misassigned_type(v, type_from_schema.wrapped)

    if isinstance(v, str):
        return v.encode("utf-8", "ignore").decode("utf-8")
    else:
        return v