def _step_microbatches(
        self,
        arg_mbs: list | None = None,
        kwarg_mbs: list | None = None,
        target_mbs: list | None = None,
        losses: list | None = None,
        return_outputs: bool = True,
    ):
        """
        Operate on the microbatches for looped schedules (multiple stages on each rank).

        TODO: Does not use sorted_batch_isend_irecv(). As a result, this schedule does
        not support models with skip connections.
        """
        arg_mbs, kwarg_mbs = self._check_inputs(arg_mbs, kwarg_mbs, target_mbs, losses)
        maybe_first_target = target_mbs[0] if target_mbs is not None else None
        self._initialize_stages(arg_mbs[0], kwarg_mbs[0], maybe_first_target)

        # Based on the plan in Step 1 created in __init__:
        # 2. Perform communication based on the pipeline_order
        stage_index_to_stage: dict[int, _PipelineStageBase] = {
            stage.stage_index: stage for stage in self._stages
        }

        # determine prev_rank and next_rank based on which ranks are next to
        # the stages in the pipeline_order
        all_prev_ranks: set[int] = set()
        all_next_ranks: set[int] = set()
        for stage_index in stage_index_to_stage:
            # TODO: assumption that stages only communicate from distances of +1/-1 (no skip connections)
            if stage_index > 0:
                all_prev_ranks.add(self.stage_index_to_group_rank[stage_index - 1])
            if stage_index < self._num_stages - 1:
                all_next_ranks.add(self.stage_index_to_group_rank[stage_index + 1])
        # count either full_backward or backward_weight together, to determine when to sync DP grads
        backward_counter: Counter[int] = Counter()
        for time_step, action in enumerate(self.pipeline_order[self.rank]):
            try:
                ops: list[dist.P2POp] = []
                if action is not None:
                    computation_type = action.computation_type
                    mb_index = action.microbatch_index
                    stage_index = action.stage_index
                    if mb_index is None:
                        raise AssertionError(
                            "All currently supported action types require valid microbatch_index"
                        )
                    if computation_type == _ComputationType.FORWARD:
                        # perform forward computation
                        stage = stage_index_to_stage[stage_index]
                        output = stage.forward_one_chunk(
                            mb_index,
                            arg_mbs[mb_index],
                            kwarg_mbs[mb_index],
                            save_forward_output=return_outputs,
                        )
                        self._maybe_compute_loss(stage, output, target_mbs, mb_index)
                        ops.extend(stage.get_fwd_send_ops(mb_index))
                    elif computation_type == _ComputationType.FULL_BACKWARD:
                        # perform backward computation
                        stage = stage_index_to_stage[stage_index]
                        loss = self._maybe_get_loss(stage, mb_index)
                        backward_counter[stage_index] += 1
                        last_backward = (
                            backward_counter[stage_index] == self._n_microbatches
                        )
                        grad_scale_factor = (
                            self._n_microbatches if self.scale_grads else 1
                        )
                        stage.backward_one_chunk(
                            mb_index,
                            loss=loss,
                            full_backward=True,
                            last_backward=last_backward,
                        )
                        if last_backward:
                            stage.scale_grads(grad_scale_factor)

                        ops.extend(stage.get_bwd_send_ops(mb_index))
                    elif computation_type == _ComputationType.BACKWARD_INPUT:
                        # perform backward computation
                        stage = stage_index_to_stage[stage_index]
                        loss = self._maybe_get_loss(stage, mb_index)
                        stage.backward_one_chunk(
                            mb_index,
                            loss=loss,
                            full_backward=False,
                            last_backward=False,
                        )
                        ops.extend(stage.get_bwd_send_ops(mb_index))
                    elif computation_type == _ComputationType.BACKWARD_WEIGHT:
                        # perform weight update
                        stage = stage_index_to_stage[stage_index]
                        backward_counter[stage_index] += 1
                        last_backward = (
                            backward_counter[stage_index] == self._n_microbatches
                        )
                        grad_scale_factor = (
                            self._n_microbatches if self.scale_grads else 1
                        )
                        stage.backward_weight_one_chunk(
                            mb_index,
                            last_backward=last_backward,
                        )
                        if last_backward:
                            stage.scale_grads(grad_scale_factor)
                    else:
                        raise ValueError(f"Unknown computation type {computation_type}")

                # Look at the neighboring ranks for this current timestep and determine whether
                # this current rank needs to do any recv communication
                for prev_rank in all_prev_ranks:
                    prev_rank_ops = self.pipeline_order[prev_rank]
                    prev_rank_action = None
                    if time_step < len(prev_rank_ops):
                        prev_rank_action = prev_rank_ops[time_step]
                    if prev_rank_action is not None:
                        computation_type = prev_rank_action.computation_type
                        mb_index = prev_rank_action.microbatch_index
                        stage_index = prev_rank_action.stage_index
                        if mb_index is None:
                            raise AssertionError(
                                "All currently supported action types require valid microbatch_index"
                            )
                        # Only handle sends for the forward from a previous rank
                        if computation_type == _ComputationType.FORWARD:
                            # If not the last stage, then receive fwd activations
                            if stage_index + 1 in stage_index_to_stage:
                                # TODO: We are assuming that stage will always receive from stage-1
                                # however that is not necessarily true of get_fwd_recv_ops
                                stage = stage_index_to_stage[stage_index + 1]
                                ops.extend(stage.get_fwd_recv_ops(mb_index))
                        elif computation_type in (
                            FULL_BACKWARD,
                            BACKWARD_INPUT,
                            BACKWARD_WEIGHT,
                        ):
                            # Previous rank doing backward has no influence for the current rank forward recv
                            pass
                        else:
                            raise ValueError(
                                f"Unknown computation type {computation_type}"
                            )
                for next_rank in all_next_ranks:
                    next_rank_ops = self.pipeline_order[next_rank]
                    next_rank_action = None
                    if time_step < len(next_rank_ops):
                        next_rank_action = next_rank_ops[time_step]
                    if next_rank_action is not None:
                        computation_type = next_rank_action.computation_type
                        mb_index = next_rank_action.microbatch_index
                        stage_index = next_rank_action.stage_index
                        if not (mb_index is not None):
                            raise AssertionError(
                                "All currently supported action types require valid microbatch_index"
                            )
                        # Only handle receives for the backwards from a next rank
                        if computation_type in (FORWARD, BACKWARD_WEIGHT):
                            # Next rank doing forward or weight update has no influence for the current rank backward recv
                            pass
                        elif computation_type in (BACKWARD_INPUT, FULL_BACKWARD):
                            # If not the first stage, then receive bwd gradients
                            if stage_index - 1 in stage_index_to_stage:
                                # TODO: We are assuming that stage will always receive from stage+1
                                # however that is not necessarily true of get_bwd_recv_ops
                                stage = stage_index_to_stage[stage_index - 1]
                                ops.extend(stage.get_bwd_recv_ops(mb_index))
                        else:
                            raise ValueError(
                                f"Unknown computation type {computation_type}"
                            )

                # do the communication
                _wait_batch_p2p(_batch_p2p(ops))
            except Exception as e:
                logger.error(
                    "[Rank %s] pipeline schedule %s caught the following exception '%s' \
at time_step %s when running action %s",
                    self.rank,
                    self.__class__.__name__,
                    e,
                    time_step,
                    action,
                )
                logger.error(
                    "%s",
                    _format_pipeline_order(
                        self.pipeline_order, error_step_number=time_step
                    ),
                )
                raise e
        # Return losses if there is a container passed in
        self._update_losses(self._stages, losses)