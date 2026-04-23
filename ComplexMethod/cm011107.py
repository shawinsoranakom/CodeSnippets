def _writeback_tensor(
        self,
        src_tensor: Tensor | None,
        dst_tensor: Tensor,
        tensor_index: int,
        expected_shape: torch.Size,
        offset: int,
        is_param: bool,  # else gradient
    ) -> None:
        """
        Write back ``src_tensor`` to ``dst_tensor`` at offset ``offset``, where ``src_tensor`` should have shape ``expected_shape``.

        ``is_param`` indicates if the tensor is the parameter (if ``True``) or gradient (if
        ``False``). If ``src_tensor`` is ``None``, then the effect is zeroing
        instead of copying. ``tensor_index`` gives the index of ``src_tensor``
        in the metadata structures.

        Raises:
            RuntimeError: If the ``src_tensor`` does not have the expected
            shape.
        """
        _p_assert(
            len(expected_shape) == 1,
            f"Expects a 1D expected shape but got {expected_shape}",
        )
        if self._debug_level == dist.DebugLevel.INFO:
            rank = self.rank if hasattr(self, "rank") else dist.get_rank()
            src_shape = src_tensor.shape if src_tensor is not None else None
            src_device = src_tensor.device if src_tensor is not None else None
            warnings.warn(
                f"[Rank {rank}] {'Parameter' if is_param else 'Gradient'} needs "
                f"writeback in {self._training_state}\n"
                f"expected shape={expected_shape} shape={src_shape} "
                f"expected device={dst_tensor.device} device={src_device}",
                stacklevel=2,
            )
        if src_tensor is not None and src_tensor.shape != expected_shape:
            # NOTE: Gradient shape mismatch is not possible in practice since
            # the gradient shape is enforced to match that of the parameter and
            # we already check for parameter shape mismatch.
            raise RuntimeError(
                f"Cannot writeback when the {'parameter' if is_param else 'gradient'} "
                f"shape changes\nExpects {expected_shape} but got {src_tensor.shape}"
            )
        if src_tensor is not None:
            dst_tensor[offset : offset + expected_shape.numel()].copy_(src_tensor)
        else:
            dst_tensor[offset : offset + expected_shape.numel()].zero_()
            if self.flat_param._is_grad_none_mask is None:
                raise AssertionError("Expected _is_grad_none_mask to be not None")
            self.flat_param._is_grad_none_mask[tensor_index] = True