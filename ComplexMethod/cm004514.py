def stride_pool(
        self,
        tensor: torch.Tensor | tuple[torch.Tensor] | list[torch.Tensor],
        axis: int | tuple[int] | list[int],
    ) -> torch.Tensor:
        """
        Perform pooling by stride slicing the tensor along the given axis.
        """
        if tensor is None:
            return None

        # Do the stride pool recursively if axis is a list or a tuple of ints.
        if isinstance(axis, (list, tuple)):
            for ax in axis:
                tensor = self.stride_pool(tensor, ax)
            return tensor

        # Do the stride pool recursively if tensor is a list or tuple of tensors.
        if isinstance(tensor, (tuple, list)):
            return type(tensor)(self.stride_pool(x, axis) for x in tensor)

        # Deal with negative axis
        axis %= tensor.ndim

        axis_slice = (
            slice(None, -1, 2) if self.config.separate_cls and self.config.truncate_seq else slice(None, None, 2)
        )
        enc_slice = tuple([slice(None)] * axis + [axis_slice])
        if self.config.separate_cls:
            cls_slice = tuple([slice(None)] * axis + [slice(None, 1)])
            tensor = torch.cat([tensor[cls_slice], tensor], axis=axis)
        return tensor[enc_slice]