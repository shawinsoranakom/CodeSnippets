def convert_to_tensors(self, tensor_type: str | TensorType | None = None, prepend_batch_axis: bool = False):
        """
        Convert the inner content to tensors.

        Args:
            tensor_type (`str` or [`~utils.TensorType`], *optional*):
                The type of tensors to use. If `str`, should be one of the values of the enum [`~utils.TensorType`]. If
                `None`, no modification is done.
            prepend_batch_axis (`int`, *optional*, defaults to `False`):
                Whether or not to add the batch dimension during the conversion.
        """
        if tensor_type is None:
            return self

        # Convert to TensorType
        if not isinstance(tensor_type, TensorType):
            tensor_type = TensorType(tensor_type)

        if tensor_type == TensorType.PYTORCH:
            if not is_torch_available():
                raise ImportError("Unable to convert output to PyTorch tensors format, PyTorch is not installed.")
            import torch

            def as_tensor(value, dtype=None):
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], np.ndarray):
                    return torch.from_numpy(np.array(value))
                if len(flatten(value)) == 0 and dtype is None:
                    dtype = torch.int64
                return torch.tensor(value, dtype=dtype)

            is_tensor = torch.is_tensor

        elif tensor_type == TensorType.MLX:
            if not is_mlx_available():
                raise ImportError("Unable to convert output to MLX tensors format, MLX is not installed.")
            import mlx.core as mx

            def as_tensor(value, dtype=None):
                if len(flatten(value)) == 0 and dtype is None:
                    dtype = mx.int32
                return mx.array(value, dtype=dtype)

            def is_tensor(obj):
                return isinstance(obj, mx.array)
        else:

            def as_tensor(value, dtype=None):
                if (
                    isinstance(value, (list, tuple))
                    and len(value) > 0
                    and isinstance(value[0], (list, tuple, np.ndarray))
                ):
                    value_lens = [len(val) for val in value]
                    if len(set(value_lens)) > 1 and dtype is None:
                        # we have a ragged list so handle explicitly
                        value = as_tensor([np.asarray(val) for val in value], dtype=object)
                if len(flatten(value)) == 0 and dtype is None:
                    dtype = np.int64
                return np.asarray(value, dtype=dtype)

            is_tensor = is_numpy_array

        # Do the tensor conversion in batch
        for key, value in self.items():
            try:
                if prepend_batch_axis:
                    value = [value]

                if not is_tensor(value):
                    tensor = as_tensor(value)

                    # Removing this for now in favor of controlling the shape with `prepend_batch_axis`
                    # # at-least2d
                    # if tensor.ndim > 2:
                    #     tensor = tensor.squeeze(0)
                    # elif tensor.ndim < 2:
                    #     tensor = tensor[None, :]

                    self[key] = tensor
            except Exception as e:
                if key == "overflowing_tokens":
                    raise ValueError(
                        "Unable to create tensor returning overflowing tokens of different lengths. "
                        "Please see if a fast version of this tokenizer is available to have this feature available."
                    ) from e
                raise ValueError(
                    "Unable to create tensor, you should probably activate truncation and/or padding with"
                    " 'padding=True' 'truncation=True' to have batched tensors with the same length. Perhaps your"
                    f" features (`{key}` in this case) have excessive nesting (inputs type `list` where type `int` is"
                    " expected)."
                ) from e

        return self