def serialize_json(
        self,
        value: Any,
        *,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> bytes:
        # What calls this code passes a value that already called
        # self._type_adapter.validate_python(value)
        # This uses Pydantic's dump_json() which serializes directly to JSON
        # bytes in one pass (via Rust), avoiding the intermediate Python dict
        # step of dump_python(mode="json") + json.dumps().
        return self._type_adapter.dump_json(
            value,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )