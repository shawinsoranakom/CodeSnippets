def from_string(cls, compile_id: str | None) -> CompileId | None:
        """
        Factory method that creates a CompileId from its string representation.
        Keep this in sync with the __str__ method.
        """
        if compile_id is None:
            return None
        try:
            for pattern in (COMPILE_ID_PATTERN, CA_COMPILE_ID_PATTERN):
                if match := pattern.match(compile_id):
                    groups = match.groupdict()
                    for k, v in groups.items():
                        if v is not None:
                            groups[k] = int(v)
                    return cls(**groups)  # type: ignore[arg-type]
            else:
                raise ValueError

        except Exception as e:
            raise ValueError(f"Invalid compile_id '{compile_id}'") from e