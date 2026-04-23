def wait_for_unshard(self):
        """
        1. In forward with implicit prefetching, to overlap the current copy-out
        with the next all-gather, we save a reference to the current all-gather
        result to free after the next copy-out.
        2. Otherwise (explicit prefetching or in backward), we free the
        all-gather result immediately after the current copy-out since we can
        already overlap the current copy-out with the previous reduce-scatter.
        """
        if not self._all_gather_result:
            return  # no preceding unshard
        async_op = self._all_gather_result.all_gather_work is not None
        if self._training_state == TrainingState.FORWARD:  # implicit prefetch
            if prev_all_gather_state := self.comm_ctx.all_gather_state:
                self._wait_all_gather_streams_on_event(prev_all_gather_state.event)
                self.comm_ctx.all_gather_state = None  # free the all-gather result
        if isinstance(self.mesh_info, FSDPMeshInfo):
            world_size = self._all_gather_process_group.size()
        else:
            world_size = 1
        if world_size == 1:
            # directly initialize unsharded parameters from sharded parameters

            for fsdp_param in self.fsdp_params:
                # Use all_gather_inputs which already handles conversion to param_dtype
                # This is consistent with the world_size > 1 path
                all_gather_input = fsdp_param.all_gather_inputs[0]

                # Make sure the all_gather_outputs has proper storage size before using it
                # First ensure we have at least one tensor in all_gather_outputs
                fsdp_param.init_all_gather_outputs(
                    [all_gather_input.numel()],
                    [all_gather_input.dtype],
                    world_size,
                    self.device,
                    force_recreate=False,
                )

                tensor = fsdp_param.all_gather_outputs[0]
                alloc_storage(tensor)

                # find alternative way to check if tensor.is_inference
                with torch.autograd._unsafe_preserve_version_counter(tensor):
                    tensor.copy_(all_gather_input)

        else:
            with record_function(self._with_fqn("FSDP::all_gather_copy_out")):
                foreach_all_gather_copy_out(
                    self._all_gather_result,
                    self.fsdp_params,
                    self._all_gather_process_group,
                )

        for fsdp_param in self.fsdp_params:
            fsdp_param.init_unsharded_param()

        self._to_unsharded()
        all_gather_copy_out_event = self.device_handle.Event()
        all_gather_copy_out_event.record()

        if (
            not async_op
            and self._training_state == TrainingState.FORWARD
            and world_size > 1
        ):
            # Defer free to allow for overlap of this copy-out with next
            # all-gather collective
            self.comm_ctx.all_gather_state = AllGatherState(
                self._all_gather_result, all_gather_copy_out_event
            )
        else:
            self._wait_all_gather_streams_on_event(all_gather_copy_out_event)

        self._all_gather_result = None