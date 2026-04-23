def _writeback_orig_params(self) -> bool:
        """
        Write back any parameters that changed storage to the handle's ``FlatParameter``.

        Iterates over the original parameters and writes back any parameters
        that changed storages (due to a non-inplace operator) to the handle's
        ``FlatParameter``. This method preserves the ``FlatParameter` 's
        device even if an original parameter's device changes.

        Raises:
            RuntimeError: If an original parameter or gradient changes storages
            but no longer has the expected flattened shape.
        Returns: ``True`` if some writeback happened, and ``False`` otherwise.
        """
        if (
            self.uses_sharded_strategy
            and not self.is_sharded(self.flat_param)
            and not self._skipped_use_sharded_views
        ):
            # For `NO_SHARD`, we may still need to writeback
            return False
        flat_param = self.flat_param
        wroteback = False
        if self._skipped_use_sharded_views and self.uses_sharded_strategy:
            # NOTE: We must use the unsharded flat parameter from which the
            # unsharded views were computed, not the one from the current
            # calling context (`_get_padded_unsharded_flat_param()`) since that
            # may be different (e.g. the model changed from train to eval).
            flat_param_tensor = self._unsharded_flat_param_for_skipped_views
            _p_assert(
                _data_ptr_allocated(flat_param_tensor),
                "If skipped using sharded views, the unsharded flat parameter "
                "should be allocated",
            )
        else:
            flat_param_tensor = flat_param
        # NOTE: Since this method is called in the pre-unshard, which is only
        # called during computation in the pre-forward or pre-backward, the
        # sharded gradient should be guaranteed to be in `.grad`, not in
        # `._saved_grad_shard`.
        flat_param_grad = (
            flat_param.grad
            if self.uses_sharded_strategy or not self._offload_params
            else flat_param._cpu_grad
        )
        for i, (
            param,
            (in_shard, offset_in_shard, numel_in_shard, _, _),
            (param_name, module, _),
        ) in enumerate(
            zip(
                flat_param._params,
                flat_param._shard_param_infos,
                flat_param._param_infos,
            )
        ):
            if not in_shard:
                continue
            if not hasattr(module, param_name):
                # Do not writeback if original parameters are deregistered
                # (e.g. during model checkpointing)
                continue

            # Check for parameter writeback
            if self._skipped_use_sharded_views:
                param = flat_param._tensors[i]
                _p_assert(
                    param is not None,
                    f"Expects to have saved tensor for {flat_param._fqns[i]}",
                )
            param_changed = getattr(module, param_name) is not param
            needs_param_writeback = (
                param_changed  # changed parameter variable itself
                or not _same_storage(param, flat_param_tensor)
            )
            if self._skipped_use_sharded_views and (
                param_changed or needs_param_writeback
            ):
                raise AssertionError(
                    "FSDP does not support changing the parameters between "
                    f"forward and backward for {self._sharding_strategy}"
                )
            if param_changed:
                # NOTE: The gradient is not preserved after a parameter change.
                param = getattr(module, param_name)
                flat_param._params[i] = param
            if needs_param_writeback:
                expected_shape = torch.Size([numel_in_shard])
                src = param if self.uses_sharded_strategy else param.view(-1)
                self._writeback_tensor(
                    src, flat_param, i, expected_shape, offset_in_shard, True
                )
                wroteback = True

            # Check for gradient writeback
            if self._skipped_use_sharded_views:
                # Skip the writeback check because we do not expose gradients
                # when we skipped using sharded views
                continue
            if param.grad is None and flat_param.grad is not None:
                expected_shape = torch.Size([numel_in_shard])
                self._writeback_tensor(
                    None, flat_param.grad, i, expected_shape, offset_in_shard, False
                )
            elif param.grad is not None:
                # For `NO_SHARD` + CPU offloading, `_cpu_grad` is always in
                # memory and owns the gradient storage, so it will never
                # require gradient writeback.
                if not self.uses_sharded_strategy and self._offload_params:
                    # Explicitly continue to handle the case of `no_sync()`,
                    # where `param.grad` is a view into the GPU gradient
                    # referenced by `flat_param.grad`, while `flat_param_grad`
                    # is `flat_param._cpu_grad`, which is on CPU
                    continue

                needs_grad_writeback = flat_param_grad is None or not _same_storage(
                    param.grad, flat_param_grad
                )
                if needs_grad_writeback:
                    if flat_param_grad is None:
                        flat_param_grad = torch.zeros_like(flat_param)
                    expected_shape = torch.Size([numel_in_shard])
                    src = (
                        param.grad
                        if self.uses_sharded_strategy
                        else param.grad.view(-1)
                    )
                    self._writeback_tensor(
                        src,
                        flat_param_grad,
                        i,
                        expected_shape,
                        offset_in_shard,
                        False,
                    )
                    flat_param.grad = flat_param_grad
                    flat_param_grad = flat_param.grad

        # TODO: If we want to handle shared parameters, we need to re-generate
        # the shared parameter data structures in case sharedness changed.
        for (
            param_name,
            module,
            _,
            prim_param_name,
            prim_module,
            _,
        ) in flat_param._shared_param_infos:
            if getattr(module, param_name) is not getattr(prim_module, prim_param_name):
                raise NotImplementedError(
                    "Changing shared parameters is not supported yet"
                )
        return wroteback