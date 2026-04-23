def post_backward(self, *unused: Any):
        # This method should be idempotent and safe to call even when this
        # FSDP parameter group was not used in backward (should be a no-op)
        logger.debug("%s", self._with_fqn("FSDP::post_backward"))
        self._training_state = TrainingState.POST_BACKWARD
        with record_function(self._with_fqn("FSDP::post_backward_accumulate")):
            for fsdp_param in self.fsdp_params:
                fsdp_param.accumulate_unsharded_grad_if_needed()
        with record_function(self._with_fqn("FSDP::post_backward_reshard")):
            if not self.reduce_grads:
                if self.reshard_after_backward:
                    self.reshard()
                for fsdp_param in self.fsdp_params:
                    fsdp_param.to_accumulated_grad_if_needed()
                return
            # Save the autograd-computed gradients before resharding to only
            # access the unsharded parameters when their data is present
            fsdp_params_with_grad: list[FSDPParam] = []
            unsharded_grads: list[torch.Tensor] = []
            for fsdp_param in self.fsdp_params:
                if not hasattr(fsdp_param, "_unsharded_param"):
                    continue
                # May have an accumulated gradient of the reduce dtype if the
                # previous backward did not reduce-scatter
                if fsdp_param.unsharded_accumulated_grad is not None:
                    fsdp_params_with_grad.append(fsdp_param)
                    unsharded_grads.append(fsdp_param.unsharded_accumulated_grad_data)
                    fsdp_param.unsharded_accumulated_grad = None
                elif fsdp_param.unsharded_param.grad is not None:
                    fsdp_params_with_grad.append(fsdp_param)
                    unsharded_grads.append(fsdp_param.unsharded_grad_data)
                    fsdp_param.unsharded_param.grad = None
            if self.reshard_after_backward:
                self.reshard()
        # Wait on prior module's RS states (assumes backward fires groups
        # N-1 first; if not, overlap degrades but correctness is preserved).
        if (
            self._param_group_index == self._num_param_groups - 1
            and self.comm_ctx.reduce_scatter_states
        ):
            with record_function(f"FSDP::post_backward_rs_wait ({self._module_fqn})"):
                for rs_state in self.comm_ctx.reduce_scatter_states:
                    if rs_state.event is not None:
                        self.device_handle.current_stream().wait_event(rs_state.event)
                self.comm_ctx.reduce_scatter_states.clear()
        if len(fsdp_params_with_grad) == 0:
            return
        with record_function(self._with_fqn("FSDP::post_backward_reduce")):
            all_reduce_pg = (
                self._all_reduce_process_group
                if isinstance(self.mesh_info, DDPMeshInfo)
                else None
            )
            all_reduce_stream: torch.cuda.Stream
            if all_reduce_pg is None and self._all_reduce_hook_stream is not None:
                # this means the native HSDP is not enabled,
                # but user may want to have a custom HSDP setup
                if self._all_reduce_hook is None:
                    raise AssertionError(
                        "all reduce hook stream is specified but hook itself is missing."
                    )
                all_reduce_stream = self._all_reduce_hook_stream
            else:
                all_reduce_stream = self.comm_ctx.all_reduce_stream

            self._wait_for_post_backward()
            (
                reduce_scatter_input,
                reduce_scatter_event,
                self._post_reduce_event,
                all_reduce_input,
                all_reduce_event,
                self._partial_reduce_output,
            ) = foreach_reduce(
                fsdp_params_with_grad,
                unsharded_grads,
                (
                    # pyrefly: ignore [bad-argument-type]
                    self._reduce_scatter_process_group
                    if isinstance(self.mesh_info, FSDPMeshInfo)
                    else None  # pyre-fixme[6]
                ),
                self.comm_ctx.reduce_scatter_stream,
                self._reduce_scatter_comm,
                self._orig_dtype,
                self._reduce_dtype,
                self.device,
                self.gradient_divide_factor,
                (
                    self._all_reduce_process_group
                    if isinstance(self.mesh_info, DDPMeshInfo)
                    else None
                ),
                all_reduce_stream,
                self.all_reduce_grads,
                self._partial_reduce_output,
                self._all_reduce_hook,
                self.force_sum_reduction_for_comms,
                self._label_suffix,
            )
            self.comm_ctx.reduce_scatter_states.append(
                ReduceScatterState(reduce_scatter_input, reduce_scatter_event)
            )
            if all_reduce_input is not None:
                if self.device.type != "cpu":
                    if all_reduce_event is None:
                        raise AssertionError(
                            "Expected all_reduce_event to be set for non-CPU device"
                        )
                self._all_reduce_state = AllReduceState(
                    all_reduce_input, all_reduce_event
                )