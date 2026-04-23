def _perform_action(action: _Action) -> None:
            comp_type = action.computation_type
            mb_index: int = (
                action.microbatch_index if action.microbatch_index is not None else -1
            )
            if not (
                mb_index >= 0
                or comp_type
                in (
                    UNSHARD,
                    RESHARD,
                    REDUCE_GRAD,
                )
            ):
                raise AssertionError(f"{action=} missing mb_index")
            stage_idx = action.stage_index
            stage = stage_index_to_stage[stage_idx]
            stage_uses_fsdp = isinstance(stage.submod, FSDPModule)
            # see [Note: V-schedule special case]
            is_next_stage_on_this_rank = stage_idx + 1 in stage_index_to_stage
            is_prev_stage_on_this_rank = stage_idx - 1 in stage_index_to_stage

            # TODO(whc) it's not actually safe to use _batch_p2p here in the uncommon case the model has skip-connections,
            # since we do not want to batch up ops between more than a pair of ranks.  _sorted_batch_p2p would be
            # safe to use instead.
            # However, I was wondering if I should avoid calling batched operators at all in the case that there is
            # only one operator per batch.  I could iterate through the 'fwd_send_ops' one by one and run them.
            if comp_type == SEND_F:
                send_ops.append(_batch_p2p(stage.get_fwd_send_ops(mb_index)))
            elif comp_type == SEND_B:
                send_ops.append(_batch_p2p(stage.get_bwd_send_ops(mb_index)))
            elif comp_type == RECV_F:
                if (stage_idx, mb_index) in self.fwd_recv_ops:
                    raise AssertionError(
                        f"Recv twice for {stage_idx=} {mb_index=} without executing forward"
                    )
                self.fwd_recv_ops[(stage_idx, mb_index)] = _batch_p2p(
                    stage.get_fwd_recv_ops(mb_index)
                )
            elif comp_type == RECV_B:
                if (stage_idx, mb_index) in self.bwd_recv_ops:
                    raise AssertionError(
                        f"Recv twice for {stage_idx=} {mb_index=} without executing backward"
                    )
                self.bwd_recv_ops[(stage_idx, mb_index)] = _batch_p2p(
                    stage.get_bwd_recv_ops(mb_index)
                )
            elif comp_type == UNSHARD:
                if stage_uses_fsdp:
                    if not (
                        stage_idx not in self.unsharded_stages
                        and stage_idx not in self.unshard_ops
                    ):
                        raise AssertionError(f"Unsharding the same {stage_idx=} twice")
                    for submodule in stage.submod.modules():
                        if not isinstance(submodule, FSDPModule):
                            continue
                        handle = cast(UnshardHandle, submodule.unshard(async_op=True))
                        self.unshard_ops[stage_idx].append(handle)
            elif comp_type == RESHARD:
                if stage_uses_fsdp:
                    if stage_idx not in self.unsharded_stages:
                        raise AssertionError(
                            f"Resharding {stage_idx=} without unsharding"
                        )
                    if stage_idx in self.unshard_ops:
                        raise AssertionError(
                            f"Resharding {stage_idx=} before finishing unshard"
                        )
                    for submodule in stage.submod.modules():
                        if not isinstance(submodule, FSDPModule):
                            continue
                        submodule.reshard()
                    self.unsharded_stages.remove(stage_idx)
            elif comp_type == FORWARD:
                self._assert_unsharded(stage)

                if (
                    not stage.is_first
                    # no recv op expected for V-schedule special case (see [Note: V-schedule special case])
                    and not is_prev_stage_on_this_rank
                ):
                    if (stage_idx, mb_index) not in self.fwd_recv_ops:
                        raise AssertionError(
                            f"Computing {action=} before receiving input"
                        )
                    _wait_batch_p2p(self.fwd_recv_ops.pop((stage_idx, mb_index)))

                output = stage.forward_one_chunk(
                    mb_index,
                    arg_mbs[mb_index],  # type: ignore[index]
                    kwarg_mbs[mb_index],  # type: ignore[index]
                    save_forward_output=return_outputs,
                )
                self._maybe_compute_loss(stage, output, target_mbs, mb_index)

                # SEND/RECV op are avoided for special case with 2 adjacent stages on same rank
                # see [Note: V-schedule special case]
                if is_next_stage_on_this_rank:
                    stage_index_to_stage[stage_idx + 1].set_local_fwd_input(
                        output, mb_index
                    )

            elif comp_type == FULL_BACKWARD:
                self._assert_unsharded(stage)

                if (
                    not stage.is_last
                    # no recv op expected for V-schedule special case (see [Note: V-schedule special case])
                    and not is_next_stage_on_this_rank
                ):
                    if (stage_idx, mb_index) not in self.bwd_recv_ops:
                        raise AssertionError(
                            f"Attempted to run compute {action=} before receiving input"
                        )
                    _wait_batch_p2p(self.bwd_recv_ops.pop((stage_idx, mb_index)))
                loss = self._maybe_get_loss(stage, mb_index)
                self.backward_counter[stage_idx] += 1
                last_backward = self.backward_counter[stage_idx] == self._n_microbatches
                stage.backward_one_chunk(
                    mb_index,
                    loss=loss,
                    full_backward=True,
                    last_backward=last_backward,
                )
                # SEND/RECV op are avoided for special case with 2 adjacent stages on same rank
                # see [Note: V-schedule special case]
                if is_prev_stage_on_this_rank:
                    stage_index_to_stage[stage_idx - 1].set_local_bwd_input(
                        stage.get_local_bwd_output(mb_index), mb_index
                    )
            elif comp_type == BACKWARD_INPUT:
                self._assert_unsharded(stage)

                if not stage.is_last and not is_next_stage_on_this_rank:
                    if (stage_idx, mb_index) not in self.bwd_recv_ops:
                        raise AssertionError(
                            f"Attempted to run compute {action=} before receiving input"
                        )
                    _wait_batch_p2p(self.bwd_recv_ops.pop((stage_idx, mb_index)))
                loss = self._maybe_get_loss(stage, mb_index)
                stage.backward_one_chunk(
                    mb_index,
                    loss=loss,
                    full_backward=False,
                    last_backward=False,
                )
                # SEND/RECV op are avoided for special case with 2 adjacent stages on same rank
                # see [Note: V-schedule special case]
                if is_prev_stage_on_this_rank:
                    stage_index_to_stage[stage_idx - 1].set_local_bwd_input(
                        stage.get_local_bwd_output(mb_index), mb_index
                    )
            elif comp_type == BACKWARD_WEIGHT:
                self._assert_unsharded(stage)
                self.backward_counter[stage_idx] += 1
                last_backward = self.backward_counter[stage_idx] == self._n_microbatches
                stage.backward_weight_one_chunk(
                    mb_index,
                    last_backward=last_backward,
                )
            elif comp_type == REDUCE_GRAD:
                grad_scale_factor = self._n_microbatches if self.scale_grads else 1
                stage.perform_reduce_grad(grad_scale_factor)
            else:
                raise ValueError(f"{action=} is unknown or unsupported")