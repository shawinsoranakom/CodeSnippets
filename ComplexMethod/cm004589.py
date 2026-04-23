def _preprocess_input(self, inputs, error_message, expected_nesting=1, dtype=None):
        """
        Preprocess input by converting torch tensors to numpy arrays and validating structure.

        Args:
            inputs: The input to process
            error_message: Error message if validation fails
            expected_nesting: Expected nesting level (1 for points/labels, 2 for boxes)
            dtype: Optional data type for numpy array conversion

        Returns:
            Processed input as list of numpy arrays or None
        """
        if inputs is None:
            return None

        # Convert torch tensor to list if applicable
        if hasattr(inputs, "numpy"):
            inputs = inputs.numpy().tolist()

        # Validate structure based on expected nesting
        valid = isinstance(inputs, list)
        current = inputs

        for _ in range(expected_nesting):
            if not valid or not current:
                break
            valid = valid and isinstance(current[0], list)
            current = current[0] if current else None

        if not valid:
            raise ValueError(error_message)

        # Convert to numpy arrays
        return [np.array(item, dtype=dtype) for item in inputs]