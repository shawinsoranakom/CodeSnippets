def init_flat_param_attributes(self) -> None:
        """
        This initializes some attributes on the handle's ``FlatParameter``.
        This should be called during lazy initialization since it requires the
        parameter to be on the compute device if not offloading to CPU and we
        want to give users the chance to move the parameter appropriately after
        the FSDP constructor.

        For each tensor attribute on the ``FlatParameter``, see the unshard and
        reshard methods in this class for the allocation and free pattern.
        """
        flat_param = self.flat_param
        if flat_param.dtype != self._orig_param_dtype:
            # Entering this branch means that the user changed the parameter
            # dtype after FSDP initialization, in which case we may need to
            # refresh some saved dtype attributes (dtypes specified as a part
            # of mixed precision take precedence).
            if not self._low_prec_param_dtype_specified:
                self._fwd_bwd_param_dtype = flat_param.dtype
            # For `reduce_dtype`, require `param_dtype` was not specified since
            # then we infer the `reduce_dtype` from the specified `param_dtype`
            if (
                not self._low_prec_reduce_dtype_specified
                and not self._low_prec_param_dtype_specified
            ):
                self._reduce_dtype = flat_param.dtype
            self._orig_param_dtype = flat_param.dtype
        cpu_device = torch.device("cpu")
        if self._offload_params:
            _p_assert(
                flat_param.device == cpu_device,
                f"Expects the `FlatParameter` to be on CPU when parameter CPU "
                f"offloading is enabled, not {flat_param.device}",
            )
        else:
            self._check_on_compute_device(self.flat_param)
        flat_param._local_shard = flat_param.data
        if self._offload_params:
            # Pin the memory for faster H2D transfer
            flat_param._local_shard = flat_param._local_shard.pin_memory()
            # Pre-allocate the sharded gradient on CPU to enable non-blocking
            # D2H transfer during the backward pass
            flat_param._cpu_grad = torch.zeros_like(
                flat_param._local_shard, device=cpu_device
            ).pin_memory()
        if self._uses_param_mixed_precision:
            # For parameter mixed precision, we maintain a low precision
            # sharded tensor on the compute device to be all-gathered (for
            # sharded strategies) or directly used (for `NO_SHARD`) for
            # computation.
            flat_param._mp_shard = torch.empty_like(
                flat_param._local_shard,
                device=self.device,
                dtype=self._fwd_bwd_param_dtype,
            )
            _free_storage(flat_param._mp_shard)
        if self.uses_sharded_strategy:
            # We maintain a padded unsharded tensor that serves as the
            # all-gather destination and owns the original parameter storages.
            unsharded_param_dtype = (
                self._fwd_bwd_param_dtype
                if self._uses_param_mixed_precision
                else flat_param.dtype
            )  # use low precision if parameter mixed precision is enabled
            padded_unsharded_numel = flat_param.numel() * self.world_size
            flat_param._full_param_padded = torch.empty(
                padded_unsharded_numel,
                device=self.device,
                dtype=unsharded_param_dtype,
            )
            flat_param._padded_unsharded_size = flat_param._full_param_padded.size()
            _free_storage(flat_param._full_param_padded)

            if self._uses_param_mixed_precision:
                # For parameter mixed precision, we maintain a full precision
                # padded unsharded tensor for when we force full precision.
                flat_param._full_prec_full_param_padded = torch.empty(
                    padded_unsharded_numel,
                    device=self.device,
                    dtype=flat_param.dtype,  # full precision
                )
                _free_storage(flat_param._full_prec_full_param_padded)