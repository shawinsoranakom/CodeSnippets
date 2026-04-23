def _validate_single_input(
        self,
        data: torch.Tensor | np.ndarray | list,
        expected_depth: int,
        input_name: str,
        expected_format: str,
        expected_coord_size: int | None = None,
    ) -> list:
        """
                Validate a single input by ensuring proper nesting and raising an error if the input is not valid.

                Args:
                    data (`torch.Tensor`, `np.ndarray`, or `list`):
                        Input data to process.
                    expected_depth (`int`):
                        Expected nesting depth.
                    input_name (`str`):
                        Name of the input for error messages.
                    expected_format (`str`):
                        The expected format of the input.
                    expected_coord_size (`int`, *optional*):
                        Expected coordinate size (4 for boxes, None for labels).
        .
        """
        if data is None:
            return None

        # Handle tensors and numpy arrays first
        if isinstance(data, (torch.Tensor, np.ndarray)):
            # For tensors/arrays, we can directly check the number of dimensions
            if data.ndim != expected_depth:
                raise ValueError(
                    f"Input {input_name} must be a tensor/array with {expected_depth} dimensions. The expected nesting format is {expected_format}. Got {data.ndim} dimensions."
                )
            elif expected_coord_size is not None:
                if data.shape[-1] != expected_coord_size:
                    raise ValueError(
                        f"Input {input_name} must be a tensor/array with {expected_coord_size} as the last dimension, got {data.shape[-1]}."
                    )
            return self._convert_to_nested_list(data, expected_depth)

        # Handle nested lists
        if isinstance(data, list):
            current_depth = self._get_nesting_level(data)
            if current_depth != expected_depth:
                raise ValueError(
                    f"Input {input_name} must be a nested list with {expected_depth} levels. The expected nesting format is {expected_format}. Got {current_depth} levels."
                )
            return self._convert_to_nested_list(data, expected_depth)