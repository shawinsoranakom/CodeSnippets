def _pre_forward(self, *inputs, **kwargs):
        if self._use_python_reducer:
            return inputs, kwargs

        if not self._lazy_init_ran and not torch.compiler.is_compiling():
            self._lazy_init()

        if self._delay_all_reduce_all_params:
            return inputs, kwargs

        if torch.is_grad_enabled() and self.require_backward_grad_sync:
            if self.logger is None:
                raise AssertionError("self.logger must not be None")
            self.logger.set_runtime_stats_and_log()
            self.reducer.prepare_for_forward()

        # Notify the join context that this process has not joined, if
        # needed
        work = Join.notify_join_context(self)
        if work:
            self.reducer._set_forward_pass_work_handle(
                work,
                self._divide_by_initial_world_size,  # type: ignore[arg-type]
            )

        # Calling _rebuild_buckets before forward computation,
        # It may allocate new buckets before deallocating old buckets
        # inside _rebuild_buckets. To save peak memory usage,
        # call _rebuild_buckets before the peak memory usage increases
        # during forward computation.
        # This should be called only once during whole training period.
        if torch.is_grad_enabled() and self.reducer._rebuild_buckets():
            logger.info("Reducer buckets have been rebuilt in this iteration.")
            self._has_rebuilt_buckets = True

        # sync params according to location (before/after forward) user
        # specified as part of hook, if hook was specified.
        if self._check_sync_bufs_pre_fwd():
            self._sync_buffers()

        if self._join_config.enable:
            # Notify joined ranks whether they should sync in backwards pass or not.
            self._check_global_requires_backward_grad_sync(is_joined_rank=False)

        if self.device_ids:
            moved_inputs, moved_kwargs = _to_kwargs(
                inputs,
                kwargs,
                torch.device(self.device_type, self.device_ids[0]),
                self.use_side_stream_for_tensor_copies,
            )
            args, kwargs = moved_inputs[0], moved_kwargs[0]
            # Cast inputs to reduced precision if needed.
            if self.mixed_precision is not None:
                args, kwargs = _cast_forward_inputs(
                    self.mixed_precision.param_dtype,
                    *args,
                    **kwargs,
                )
            return args, kwargs
        else:
            # Cast inputs to reduced precision if needed.
            # TODO (rohan-varma) test this codepath.
            if self.mixed_precision is not None:
                inputs, kwargs = _cast_forward_inputs(
                    self.mixed_precision.param_dtype,
                    *inputs,
                    **kwargs,
                )
            return inputs, kwargs