def _convert_to_nested_list(self, data, expected_depth, current_depth=0):
        """
        Recursively convert various input formats (tensors, numpy arrays, lists) to nested lists.
        Preserves None values within lists.

        Args:
            data: Input data in any format (may be None or contain None values)
            expected_depth: Expected nesting depth
            current_depth: Current depth in recursion

        Returns:
            Nested list representation of the data (or None)
        """
        if data is None:
            return None

        # Convert tensor/numpy to list if we're at a leaf level or if it's a multi-dimensional array
        if isinstance(data, torch.Tensor):  # PyTorch tensor
            if current_depth == expected_depth - 2 or len(data.shape) <= 2:  # At coordinate level or small tensor
                return data.numpy().tolist()
            else:
                return [self._convert_to_nested_list(item, expected_depth, current_depth + 1) for item in data]
        elif isinstance(data, np.ndarray):  # NumPy array
            if current_depth == expected_depth - 2 or len(data.shape) <= 2:  # At coordinate level or small array
                return data.tolist()
            else:
                return [self._convert_to_nested_list(item, expected_depth, current_depth + 1) for item in data]
        elif isinstance(data, list):
            if current_depth == expected_depth:
                # We've reached the expected depth, return as is
                return data
            else:
                # Continue recursion, preserving None values
                return [
                    self._convert_to_nested_list(item, expected_depth, current_depth + 1) if item is not None else None
                    for item in data
                ]
        elif isinstance(data, (int, float)):
            return data
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")