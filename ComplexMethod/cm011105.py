def _use_sharded_grad_views(self) -> None:
        """
        Set the original parameter variables' gradients to be flattened views into the sharded flat parameter's gradient.

        This is a no-op if there is no gradient.

        Parameters whose data is not present in the sharded flat parameter and
        parameters with ``requires_grad=False`` have their gradients set to
        ``None``. Since the gradient variables do not need to be preserved,
        this method does not manipulate existing ``Tensor`` data directly and
        creates new ``Tensor`` variables instead.
        """
        flat_param = self.flat_param
        self._check_sharded(flat_param)
        grad = self.sharded_grad
        if grad is None:
            for param in chain(flat_param._params, flat_param._shared_params):
                param.grad = None
            return
        self._check_sharded(grad)
        for param, shard_param_info, is_grad_none in zip(
            flat_param._params,
            flat_param._shard_param_infos,
            flat_param._is_grad_none_mask,
        ):
            if not shard_param_info.in_shard:
                param.grad = None
            else:
                numel_in_shard = shard_param_info.numel_in_shard
                if param.requires_grad and not is_grad_none:
                    offset = shard_param_info.offset_in_shard
                    if self._keep_low_precision_grads or param.dtype != grad.dtype:
                        # NOTE: This is a hack using `.data` to side step the
                        # check that parameter/gradient dtypes match. Here,
                        # `param` has full precision; `grad` has low precision.
                        if param.grad is None:
                            # `.grad` must have the same shape as `param`
                            param.grad = torch.empty_like(param)
                        param.grad.data = grad[
                            offset : offset + numel_in_shard
                        ].reshape(param.shape)
                    else:
                        param.grad = grad[offset : offset + numel_in_shard].reshape(
                            param.shape
                        )
                else:
                    param.grad = None
        if flat_param._shared_params is None:
            raise AssertionError("Expected _shared_params to be not None")
        for param, (_, _, _, prim_param_name, prim_module, _) in zip(
            flat_param._shared_params, flat_param._shared_param_infos
        ):
            in_sharded_flat_param = hasattr(prim_module, prim_param_name)
            if in_sharded_flat_param and param.requires_grad:
                prim_param = getattr(prim_module, prim_param_name)
                param.grad = prim_param.grad  # share the same reference
            else:
                param.grad = None