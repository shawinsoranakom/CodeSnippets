def _track_dim_from_dims(
        val: None | int | _DimHint | Dim,
    ) -> None | int | str:
        """
        Tracks dims, ranges, derived dims from the standardized dynamic_shapes spec.
        """
        if val is None or isinstance(val, int):  # non-tensor input or static
            return val
        if isinstance(val, _DimHint):  # store enum as string
            return val.__class__.__name__ + "." + val.type.name

        if not isinstance(val, Dim):
            raise AssertionError(f"expected Dim, got {type(val)}")

        # track root dim
        root = val.root if isinstance(val, _DerivedDim) else val  # type: ignore[attr-defined]
        if root.__name__ not in dims:
            dims[root.__name__] = {
                "min": root.min,  # type: ignore[attr-defined,union-attr]
                "max": root.max,  # type: ignore[attr-defined,union-attr]
                "derived": set(),
            }

        # track derived dims
        if isinstance(val, _DerivedDim):
            dims[root.__name__]["derived"].add(val.__name__)

        return val.__name__