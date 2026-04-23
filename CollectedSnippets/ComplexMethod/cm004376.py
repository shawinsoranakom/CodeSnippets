def convert_to_tensors(self, tensor_type: str | TensorType | None = None, **kwargs):
        """
        Convert the inner content to tensors.

        Args:
            tensor_type (`str` or [`~utils.TensorType`], *optional*):
                The type of tensors to use. If `str`, should be one of the values of the enum [`~utils.TensorType`]. If
                `None`, no modification is done.
        """
        if tensor_type is None:
            return self

        is_tensor, as_tensor = self._get_is_as_tensor_fns(tensor_type=tensor_type)

        def _convert_tensor(elem):
            if is_tensor(elem):
                return elem
            return as_tensor(elem)

        def _safe_convert_tensor(elem):
            try:
                return _convert_tensor(elem)
            except:  # noqa E722
                if key == "overflowing_values":
                    raise ValueError("Unable to create tensor returning overflowing values of different lengths. ")
                raise ValueError(
                    "Unable to create tensor, you should probably activate padding "
                    "with 'padding=True' to have batched tensors with the same length."
                )

        # Do the tensor conversion in batch
        for key, value in self.items():
            if isinstance(value, list) and isinstance(value[0], list):
                # list[list[Any]] -> list[list[Tensor]]
                self[key] = [[_safe_convert_tensor(elem) for elem in elems] for elems in value]
            elif isinstance(value, list):
                # list[Any] -> list[Tensor]
                self[key] = [_safe_convert_tensor(elem) for elem in value]
            else:
                # Any -> Tensor
                self[key] = _safe_convert_tensor(value)
        return self