def forward_callback(action: _Action, ctx: _PipelineContext):
            """Custom callback for FORWARD computation that mimics the original implementation."""
            schedule = ctx.schedule_ref
            if not isinstance(schedule, _PipelineScheduleRuntime):
                raise AssertionError(
                    f"Expected _PipelineScheduleRuntime, got {type(schedule)}"
                )
            stage_index_to_stage: dict[int, _PipelineStageBase] = {
                stage.stage_index: stage for stage in schedule._stages
            }
            stage = stage_index_to_stage[action.stage_index]
            stage_index = stage.stage_index
            mb_index = action.microbatch_index
            if mb_index is None:
                raise AssertionError("Expected mb_index to not be None")
            fwd_recv_ops = schedule.fwd_recv_ops
            arg_mbs = ctx.arg_mbs
            kwarg_mbs = ctx.kwarg_mbs

            is_next_stage_on_this_rank = stage_index + 1 in stage_index_to_stage
            is_prev_stage_on_this_rank = stage_index - 1 in stage_index_to_stage

            # used in verification at the end
            forward_calls.append((stage_index, mb_index))

            if (
                not stage.is_first
                # no recv op expected for V-schedule special case (see [Note: V-schedule special case])
                and not is_prev_stage_on_this_rank
            ):
                if (stage_index, mb_index) not in fwd_recv_ops:
                    raise AssertionError(f"Computing {action=} before receiving input")
                from torch.distributed.pipelining.schedules import _wait_batch_p2p

                _wait_batch_p2p(fwd_recv_ops.pop((stage_index, mb_index)))

            output = stage.forward_one_chunk(
                mb_index,
                arg_mbs[mb_index],  # type: ignore[index]
                kwarg_mbs[mb_index],  # type: ignore[index]
            )
            schedule._maybe_compute_loss(stage, output, ctx.target_mbs, mb_index)

            # SEND/RECV op are avoided for special case with 2 adjacent stages on same rank
            # see [Note: V-schedule special case]
            if is_next_stage_on_this_rank:
                stage_index_to_stage[stage_index + 1].set_local_fwd_input(
                    output, mb_index
                )