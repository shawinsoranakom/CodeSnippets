def validate(
        self,
        value: Any,
        values: dict[str, Any] = {},  # noqa: B006
        *,
        loc: tuple[int | str, ...] = (),
    ) -> tuple[Any, list[dict[str, Any]]]:
        try:
            return (
                self._type_adapter.validate_python(value, from_attributes=True),
                [],
            )
        except ValidationError as exc:
            return None, _regenerate_error_with_loc(
                errors=exc.errors(include_url=False), loc_prefix=loc
            )