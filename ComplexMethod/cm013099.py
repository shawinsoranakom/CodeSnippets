def is_axes(x) -> bool:
        return (
            isinstance(x, dict)
            and all(
                isinstance(k, int)
                and (v is None or isinstance(v, (Dim, _DimHint, str, int)))
                for k, v in x.items()
            )
        ) or (
            isinstance(x, (list, tuple))
            and all(v is None or isinstance(v, (Dim, _DimHint, str, int)) for v in x)
        )