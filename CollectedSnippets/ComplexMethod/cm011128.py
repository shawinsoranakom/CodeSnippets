def _root_post_backward_final_callback(self) -> None:
        logger.debug("FSDP::root_post_backward")
        with torch.profiler.record_function("FSDP::root_post_backward_callback"):
            for state in self._state_ctx.all_states:
                # Reverse so that the last param group (which gates the
                # reduce-scatter wait/clear) fires first, matching the
                # autograd backward order and preserving RS overlap for
                # per-param-mesh modules whose inputs lack gradients.
                for fsdp_param_group in reversed(state._fsdp_param_groups):
                    if fsdp_param_group._training_state != TrainingState.POST_BACKWARD:
                        # Run post-backward in case forward inputs did not require
                        # gradient so the autograd backward did not run
                        fsdp_param_group.post_backward()
                    fsdp_param_group._training_state = TrainingState.IDLE
                state._training_state = TrainingState.IDLE
                if self._state_ctx.is_last_backward:
                    state._finalize_backward()
            if self._state_ctx.is_last_backward:
                self._comm_ctx.post_forward_order.clear()
                # Catch the last module's RS states that no subsequent
                # module's group N-1 wait will clear.
                for rs_state in self._comm_ctx.reduce_scatter_states:
                    if rs_state.event is not None:
                        self._device_handle.current_stream().wait_event(rs_state.event)
                self._comm_ctx.reduce_scatter_states.clear()
            self._state_ctx.post_backward_final_callback_queued = False