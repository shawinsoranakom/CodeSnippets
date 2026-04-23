def _create_column_definitions(
    schema: SchemaMetaclass,
    bases: tuple[type],
    schema_properties: SchemaProperties,
) -> dict[str, ColumnSchema]:
    localns = locals()
    #  Update locals to handle recursive Schema definitions
    localns[schema.__name__] = schema
    annotations = get_type_hints(schema, localns=localns)
    fields = _cls_fields(schema)
    for base in bases:
        if not isinstance(base, SchemaMetaclass):
            continue
        for column_name, column_schema in base.__columns__.items():
            if column_name not in fields:
                fields[column_name] = column_schema.to_definition()

    columns = {}

    for column_name, annotation in annotations.items():
        col_dtype = dt.wrap(annotation)
        column = fields.pop(column_name, column_definition(dtype=col_dtype))

        if not isinstance(column, ColumnDefinition):
            raise ValueError(
                f"`{column_name}` should be a column definition, found {type(column)}"
            )

        dtype = column.dtype
        if dtype is None:
            dtype = col_dtype

        if col_dtype != dtype:
            raise TypeError(
                f"type annotation of column `{column_name}` does not match column definition"
            )

        column_name = column.name or column_name

        def _get_column_property(property_name: str, default: Any) -> Any:
            match (
                getattr(column, property_name),
                getattr(schema_properties, property_name),
            ):
                case (None, None):
                    return default
                case (None, schema_property):
                    return schema_property
                case (column_property, None):
                    return column_property
                case (column_property, schema_property):
                    if column_property != schema_property:
                        raise ValueError(
                            f"ambiguous property; schema property `{property_name}` has"
                            + f" value {schema_property!r} but column"
                            + f" `{column_name}` got {column_property!r}"
                        )
                    return column_property

        columns[column_name] = ColumnSchema(
            primary_key=column.primary_key,
            default_value=column.default_value,
            dtype=dt.wrap(dtype),
            name=column_name,
            append_only=_get_column_property("append_only", False),
            description=column.description,
            example=column.example,
            source_component=column.source_component,
        )

    if fields:
        names = ", ".join(fields.keys())
        raise ValueError(f"definitions of columns {names} lack type annotation")

    return columns