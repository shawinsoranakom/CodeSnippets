def prepare_gradient_for_optim(self):
        """Prepare the gradient for optimizer computation by moving the sharded gradient to the ``.grad`` attribute."""

        def cast_grad_to_param_dtype_if_needed(flat_param):
            # TODO (rohan-varma): test for full precision with keep_low_precision_grads
            if not self._force_full_precision and self._keep_low_precision_grads:
                _p_assert(flat_param.grad is not None, "Unexpected None grad!")
                if flat_param.grad.dtype != self._fwd_bwd_param_dtype:
                    flat_param.grad.data = flat_param.grad.to(self._fwd_bwd_param_dtype)
                    if self._use_orig_params:
                        self._use_sharded_grad_views()

        flat_param = self.flat_param
        # TODO (awgu): We should replace these conditional checks to encode
        # the logical intention more directly.
        if hasattr(flat_param, "_cpu_grad"):
            # NOTE: This branch includes `NO_SHARD`.
            self._check_sharded(flat_param)
            self._check_on_cpu(flat_param)
            flat_param.grad = flat_param._cpu_grad  # type: ignore[attr-defined]
            cast_grad_to_param_dtype_if_needed(flat_param)
        elif hasattr(flat_param, "_saved_grad_shard"):
            self._check_sharded(flat_param)
            self._check_on_compute_device(flat_param)
            if flat_param._saved_grad_shard is not None:
                self._check_on_compute_device(flat_param._saved_grad_shard)  # type: ignore[attr-defined]
            # If no sharded gradient was computed this iteration, then there is
            # no need to forward `_saved_grad_shard` to `grad`
            if flat_param._post_backward_called:  # type: ignore[attr-defined]
                flat_param.grad = flat_param._saved_grad_shard  # type: ignore[attr-defined]
                if flat_param.grad is not None:
                    cast_grad_to_param_dtype_if_needed(flat_param)
        else:
            _p_assert(
                not self.uses_sharded_strategy or not flat_param._post_backward_called,  # type: ignore[attr-defined]
                "All sharded parameters that received a gradient in the "
                "post-backward should use `_saved_grad_shard`",
            )
        # Delete `_saved_grad_shard` since its existence indicates a previous
        # gradient to accumulate with in the post-backward hook
        if hasattr(flat_param, "_saved_grad_shard"):
            delattr(flat_param, "_saved_grad_shard")