def unshard(self, async_op: bool = False):
        if self._all_gather_result is not None:  # already called, pending wait
            return
        if self.is_unsharded:
            return  # no-op
        if (
            not self.unshard_in_backward
            and self._training_state == TrainingState.PRE_BACKWARD
        ):
            return
        if self._reshard_after_forward_event is not None:
            # Resharded parameter data is allocated in the default stream and
            # used in the all-gather streams
            self._wait_all_gather_streams_on_event(self._reshard_after_forward_event)
            self._reshard_after_forward_event = None

        if isinstance(self.mesh_info, FSDPMeshInfo):
            world_size = self._all_gather_process_group.size()
        else:
            world_size = 1
        if world_size == 1:
            # can't skip due to early return in wait_for_unshard if
            # no self._all_gather_result
            self._all_gather_result = AllGatherResult(
                all_gather_output=self._all_gather_output,
                all_gather_event=self.device_handle.Event().record(),
                all_gather_work=None,
                param_all_gather_input_dtypes=[],
                param_all_gather_input_numels=[],
                all_gather_input_split_sizes=[],
            )

            return

        with record_function(self._with_fqn("FSDP::all_gather")):
            self._all_gather_result = foreach_all_gather(
                self.fsdp_params,
                self._all_gather_process_group,
                async_op,
                *self.comm_ctx.get_all_gather_streams(async_op, self._training_state),
                self.device,
                self._all_gather_comm,
                self._label_suffix,
            )