def _validate_tensor_shape_expected(
        self,
        actual_shape: tuple[int, ...],
        expected_shape: tuple[int | str, ...],
        field_name: str,
        shape_env: dict[str, int],
        dynamic_dims: set[str],
    ) -> None:
        """Validate that the actual tensor shape matches the expected shape."""

        if len(actual_shape) != len(expected_shape):
            raise ValueError(
                f"{field_name} has rank {len(actual_shape)} "
                f"but expected {len(expected_shape)}. "
                f"Expected shape: {expected_shape}, "
                f"but got {actual_shape}"
            )

        for i, dim in enumerate(expected_shape):
            if dim in dynamic_dims:
                continue
            elif isinstance(dim, int):
                if actual_shape[i] != dim:
                    raise ValueError(
                        f"{field_name} dim[{i}] expected "
                        f"{dim}, got {actual_shape[i]}. "
                        f"Expected shape: {expected_shape}, "
                        f"but got {actual_shape}"
                    )
            elif isinstance(dim, str):
                if dim in shape_env:
                    if actual_shape[i] != shape_env[dim]:
                        raise ValueError(
                            f"{field_name} dim[{i}] expected "
                            f"'{dim}'={shape_env[dim]}, got "
                            f"{actual_shape[i]}"
                        )
                else:
                    shape_env[dim] = actual_shape[i]
            else:
                raise TypeError(
                    f"{field_name} dim[{i}] has unsupported type: {type(dim)}"
                )