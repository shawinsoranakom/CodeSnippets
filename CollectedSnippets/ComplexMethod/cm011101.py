def _use_sharded_flat_param(self) -> None:
        """Switches to using the sharded flat parameter."""
        flat_param = self.flat_param
        if self._use_orig_params:
            in_forward = self._training_state == HandleTrainingState.FORWARD
            skip_use_sharded_views = (
                torch.is_grad_enabled()
                and in_forward
                and self._sharding_strategy
                in NO_RESHARD_AFTER_FORWARD_HANDLE_STRATEGIES
            )
            # Only incur the extra `.data` call if needed
            if skip_use_sharded_views:
                unsharded_flat_param = flat_param.data
        if self._offload_params:
            device = flat_param._local_shard.device  # type: ignore[attr-defined]
            _p_assert(
                device == torch.device("cpu"),
                f"Expects the local shard to be on CPU but got {device}",
            )
        flat_param.data = flat_param._local_shard  # type: ignore[attr-defined]
        if self._use_orig_params:
            if skip_use_sharded_views:  # type: ignore[possibly-undefined]
                self._unsharded_flat_param_for_skipped_views = unsharded_flat_param  # type: ignore[possibly-undefined]
            else:
                self._use_sharded_views()
            # For the post-forward reshard, we may try to use sharded gradient
            # views (or unsharded gradient views if a gradient was accumulated
            # in `no_sync()`), but for the post-backward reshard, we delay the
            # call to after the reduce-scatter.
            if (
                in_forward  # type: ignore[possibly-undefined]
                # Skip using gradient views if skipped using sharded views
                # since exposing unsharded parameters with sharded gradients
                # may be confusing to the user
                and not self._skipped_use_sharded_views
            ):
                # TODO: Change `_unpadded_unsharded_size` if we change the
                # gradient to be computed directly with padding.
                accumulated_grad_in_no_sync = (
                    flat_param.grad is not None
                    and self.uses_sharded_strategy
                    and flat_param.grad.shape == flat_param._unpadded_unsharded_size
                )
                if accumulated_grad_in_no_sync:
                    self._use_unsharded_grad_views()
                else:
                    self._use_sharded_grad_views()