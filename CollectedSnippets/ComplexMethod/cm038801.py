def _validate_field(
        self,
        value: object,
        field_name: str,
        expected_shape: tuple[int | str, ...],
        dynamic_dims: set[str],
        leading_idxs: tuple[int, ...] = (),
    ) -> tuple[int, ...]:
        """Validate a field and return the actual shape."""
        if isinstance(value, (int, float)):
            return ()  # Scalar
        if isinstance(value, torch.Tensor):
            return value.shape

        if not isinstance(value, (list, tuple)):
            raise TypeError(
                f"{field_name}{self._fmt_indexer(leading_idxs)} is not "
                f"one of the expected types: int, float, Tensor, list, tuple. "
                f"Got: {type(value)}"
            )

        if len(value) == 0:
            raise ValueError(
                f"{field_name}{self._fmt_indexer(leading_idxs)} is an empty sequence"
            )

        # Ensure all tensors in the list have the same
        # shape, besides dynamic dimensions
        for i, v in enumerate(value):
            shape = self._validate_field(
                v,
                field_name,
                expected_shape[1:],
                dynamic_dims,
                leading_idxs=leading_idxs + (i,),
            )

            if i == 0:
                first_shape = shape
            elif not self._match_shape_with_dynamic(
                shape,
                first_shape,
                expected_shape,
                dynamic_dims,
            ):
                raise ValueError(
                    f"{field_name}{self._fmt_indexer(leading_idxs)} "
                    f"contains inconsistent shapes: {first_shape} "
                    f"(index 0) vs {shape} (index {i})"
                )

        # Treat the list as a stacked tensor:
        # shape = (len(list), *tensor.shape)
        return (len(value),) + first_shape