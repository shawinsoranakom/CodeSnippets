def pre_unshard(self) -> bool:
        """
        Return ``False`` if this is a no-op and ``True`` otherwise.

        Postcondition: ``self.flat_param`` 's data is on the device for
        communication and is what should be all-gathered. This means that it
        matches the dtype of the expected unsharded parameter.
        """
        if (
            self._training_state == HandleTrainingState.SUMMON_FULL_PARAMS
            and self._skipped_use_sharded_views
        ):
            # Since this path imposes special semantics for the unsharded flat
            # parameter (e.g. forcing full precision), use sharded views to
            # reuse the existing logic for that special handling
            self._use_sharded_views()
        ret = False
        if self._use_orig_params and not self._skip_writeback_check:
            # Wait for the compute stream since _writeback_orig_params reads
            # original parameters that may still be in use during prefetch.
            self._device_handle.current_stream().wait_stream(
                not_none(self._compute_stream)
            )
            ret = self._writeback_orig_params()
        if (
            self.uses_sharded_strategy
            and not self._offload_params
            and not self.needs_unshard()
        ):
            pass  # no-op
        elif self._uses_param_mixed_precision and not self._force_full_precision:
            self._use_low_precision_shard()
            ret = True
        elif self._offload_params and self.flat_param.device != self.device:
            # NOTE: This creates a new tensor distinct from any attributes.
            self.flat_param_to(self.device, non_blocking=True)
            ret = True
        self._check_on_compute_device(self.flat_param)
        return ret