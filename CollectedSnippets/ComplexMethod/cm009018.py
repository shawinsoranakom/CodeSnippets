def __init__(
        self,
        schema: type[SchemaT] | dict[str, Any],
        *,
        name: str | None = None,
        description: str | None = None,
        strict: bool | None = None,
    ) -> None:
        """Initialize `SchemaSpec` with schema and optional parameters.

        Args:
            schema: Schema to describe.
            name: Optional name for the schema.
            description: Optional description for the schema.
            strict: Whether to enforce strict validation of the schema.

        Raises:
            ValueError: If the schema type is unsupported.
        """
        self.schema = schema

        if name:
            self.name = name
        elif isinstance(schema, dict):
            self.name = str(schema.get("title", f"response_format_{str(uuid.uuid4())[:4]}"))
        else:
            self.name = str(getattr(schema, "__name__", f"response_format_{str(uuid.uuid4())[:4]}"))

        self.description = description or (
            schema.get("description", "")
            if isinstance(schema, dict)
            else getattr(schema, "__doc__", None) or ""
        )

        self.strict = strict

        if isinstance(schema, dict):
            self.schema_kind = "json_schema"
            self.json_schema = schema
        elif isinstance(schema, type) and issubclass(schema, BaseModel):
            self.schema_kind = "pydantic"
            self.json_schema = schema.model_json_schema()
        elif is_dataclass(schema):
            self.schema_kind = "dataclass"
            self.json_schema = TypeAdapter(schema).json_schema()
        elif is_typeddict(schema):
            self.schema_kind = "typeddict"
            self.json_schema = TypeAdapter(schema).json_schema()
        else:
            msg = (
                f"Unsupported schema type: {type(schema)}. "
                f"Supported types: Pydantic models, dataclasses, TypedDicts, and JSON schema dicts."
            )
            raise ValueError(msg)