def _exec(self, funcs: Iterable, v: Any, path: list[Hashable] | None = None) -> Any:
        """Execute the validation functions."""
        errors: list[vol.Invalid] = []
        for func in funcs:
            try:
                if path is None:
                    return func(v)
                return func(path, v)
            except vol.Invalid as e:
                errors.append(e)
        if errors:
            raise next(
                (err for err in errors if "extra keys not allowed" not in err.msg),
                errors[0],
            )
        raise vol.AnyInvalid(self.msg or "no valid value found", path=path)