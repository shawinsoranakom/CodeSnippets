def overlap_callback(action: _Action, ctx: _PipelineContext):
            """Custom callback for OVERLAP_F_B computation that mimics the original implementation."""
            schedule = ctx.schedule_ref
            if not isinstance(schedule, _PipelineScheduleRuntime):
                raise AssertionError(
                    f"Expected _PipelineScheduleRuntime, got {type(schedule)}"
                )
            stage_index_to_stage: dict[int, _PipelineStageBase] = {
                stage.stage_index: stage for stage in schedule._stages
            }
            if action.sub_actions is None:
                raise AssertionError("Expected action.sub_actions to not be None")
            fwd_action = action.sub_actions[0]
            bwd_action = action.sub_actions[1]

            # Forward ========================================================
            forward_callback(fwd_action, ctx)
            overlap_calls.append(
                (
                    fwd_action.stage_index,
                    fwd_action.microbatch_index,
                    bwd_action.stage_index,
                    bwd_action.microbatch_index,
                )
            )

            # Backward ========================================================
            backward_stage_index = bwd_action.stage_index
            backward_stage = stage_index_to_stage[backward_stage_index]
            backward_mb_index = bwd_action.microbatch_index
            if backward_mb_index is None:
                raise AssertionError("Expected backward_mb_index to not be None")
            bwd_recv_ops = schedule.bwd_recv_ops
            is_next_stage_on_this_rank = (
                backward_stage.stage_index + 1 in stage_index_to_stage
            )
            is_prev_stage_on_this_rank = (
                backward_stage.stage_index - 1 in stage_index_to_stage
            )
            if (
                not backward_stage.is_last
                # no recv op expected for V-schedule special case (see [Note: V-schedule special case])
                and not is_next_stage_on_this_rank
            ):
                if (backward_stage_index, backward_mb_index) not in bwd_recv_ops:
                    raise AssertionError(
                        f"Attempted to run compute {action=} before receiving input"
                    )
                _wait_batch_p2p(
                    bwd_recv_ops.pop((backward_stage_index, backward_mb_index))
                )
            loss = schedule._maybe_get_loss(backward_stage, backward_mb_index)
            schedule.backward_counter[backward_stage_index] += 1
            last_backward = (
                schedule.backward_counter[backward_stage_index]
                == schedule._n_microbatches
            )
            grad_scale_factor = schedule._n_microbatches if schedule.scale_grads else 1
            backward_stage.backward_one_chunk(
                backward_mb_index,
                loss=loss,
                full_backward=True,
                last_backward=last_backward,
            )
            if last_backward:
                backward_stage.scale_grads(grad_scale_factor)
            # SEND/RECV op are avoided for special case with 2 adjacent stages on same rank
            # see [Note: V-schedule special case]
            if is_prev_stage_on_this_rank:
                stage_index_to_stage[backward_stage_index - 1].set_local_bwd_input(
                    backward_stage.get_local_bwd_output(backward_mb_index),
                    backward_mb_index,
                )