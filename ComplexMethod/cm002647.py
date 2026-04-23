def convert_to_tensors(
        self,
        tensor_type: str | TensorType | None = None,
        skip_tensor_conversion: list[str] | set[str] | None = None,
    ):
        """
        Convert the inner content to tensors.

        Args:
            tensor_type (`str` or [`~utils.TensorType`], *optional*):
                The type of tensors to use. If `str`, should be one of the values of the enum [`~utils.TensorType`]. If
                `None`, no modification is done.
            skip_tensor_conversion (`list[str]` or `set[str]`, *optional*):
                List or set of keys that should NOT be converted to tensors, even when `tensor_type` is specified.

        Note:
            Values that don't have an array-like structure (e.g., strings, dicts, lists of strings) are
            automatically skipped and won't be converted to tensors. Ragged arrays (lists of arrays with
            different lengths) are still attempted, though they may raise errors during conversion.
        """
        if tensor_type is None:
            return self

        is_tensor, as_tensor = self._get_is_as_tensor_fns(tensor_type)
        skip_tensor_conversion = (
            skip_tensor_conversion if skip_tensor_conversion is not None else self.skip_tensor_conversion
        )

        # Do the tensor conversion in batch
        for key, value in self.items():
            # Skip keys explicitly marked for no conversion
            if skip_tensor_conversion and key in skip_tensor_conversion:
                continue

            # Skip values that are not array-like
            if not _is_tensor_or_array_like(value):
                continue

            try:
                if not is_tensor(value):
                    tensor = as_tensor(value)
                    self[key] = tensor
            except Exception as e:
                if key == "overflowing_values":
                    raise ValueError(
                        f"Unable to create tensor for '{key}' with overflowing values of different lengths. "
                        f"Original error: {str(e)}"
                    ) from e
                raise ValueError(
                    f"Unable to convert output '{key}' (type: {type(value).__name__}) to tensor: {str(e)}\n"
                    f"You can try:\n"
                    f"  1. Use padding=True to ensure all outputs have the same shape\n"
                    f"  2. Set return_tensors=None to return Python objects instead of tensors"
                ) from e

        return self