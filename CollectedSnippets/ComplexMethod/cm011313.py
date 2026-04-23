def _calculate_single_rank_operations(self, rank) -> list[_Action | None]:
        # max(2 * self.pp_group_size - 1, ...) ensure the number of microbatches is at least
        # as large of the number of microbatches needed to fully utilize the pipeline
        n_micro = max(2 * self.pp_group_size - 1, self._n_microbatches)
        rank_ops: list[_Action | None] = [None for _ in range(rank)]

        # Forward and backward action counts for stage chunk 0 and chunk 1
        f0_cnt, f1_cnt, b0_cnt, b1_cnt = 0, 0, 0, 0
        # warm-up phase
        warmup_n1 = 2 * (self.pp_group_size - rank) - 1
        stage_id_chunk0 = rank
        stage_id_chunk1 = self.num_stages - 1 - rank

        for _ in range(warmup_n1):
            rank_ops.append(
                _Action(stage_id_chunk0, computation_type=F, microbatch_index=f0_cnt)
            )
            f0_cnt += 1
        warmup_n2 = rank
        for _ in range(warmup_n2):
            rank_ops.append(
                _Action(stage_id_chunk1, computation_type=F, microbatch_index=f1_cnt)
            )
            f1_cnt += 1
            rank_ops.append(
                _Action(stage_id_chunk0, computation_type=F, microbatch_index=f0_cnt)
            )
            f0_cnt += 1
        warmup_n3 = self.pp_group_size - rank
        for _ in range(warmup_n3):
            rank_ops.append(
                _Action(stage_id_chunk1, computation_type=F, microbatch_index=f1_cnt)
            )
            f1_cnt += 1
            rank_ops.append(
                _Action(stage_id_chunk1, computation_type=I, microbatch_index=b1_cnt)
            )
            rank_ops.append(
                _Action(stage_id_chunk1, computation_type=W, microbatch_index=b1_cnt)
            )
            b1_cnt += 1
        # stable phase
        while f1_cnt < f0_cnt or f0_cnt < n_micro:
            if f0_cnt < n_micro:
                rank_ops.append(
                    _Action(
                        stage_id_chunk0, computation_type=F, microbatch_index=f0_cnt
                    )
                )
                f0_cnt += 1
            rank_ops.append(
                _Action(stage_id_chunk0, computation_type=I, microbatch_index=b0_cnt)
            )
            rank_ops.append(
                _Action(stage_id_chunk0, computation_type=W, microbatch_index=b0_cnt)
            )
            b0_cnt += 1

            rank_ops.append(
                _Action(stage_id_chunk1, computation_type=F, microbatch_index=f1_cnt)
            )
            f1_cnt += 1
            rank_ops.append(
                _Action(stage_id_chunk1, computation_type=I, microbatch_index=b1_cnt)
            )
            rank_ops.append(
                _Action(stage_id_chunk1, computation_type=W, microbatch_index=b1_cnt)
            )
            b1_cnt += 1
        # cool-down phase
        w0_cnt, w1_cnt = b0_cnt, b1_cnt
        cooldown_n1 = rank
        for _ in range(cooldown_n1):
            rank_ops.append(
                _Action(stage_id_chunk0, computation_type=I, microbatch_index=b0_cnt)
            )
            b0_cnt += 1
            rank_ops.append(
                _Action(stage_id_chunk1, computation_type=I, microbatch_index=b1_cnt)
            )
            b1_cnt += 1
        cooldown_n2 = self.pp_group_size - rank
        for _ in range(cooldown_n2):
            rank_ops.append(
                _Action(stage_id_chunk0, computation_type=I, microbatch_index=b0_cnt)
            )
            b0_cnt += 1
            rank_ops.append(
                _Action(stage_id_chunk0, computation_type=W, microbatch_index=w0_cnt)
            )
            w0_cnt += 1
        while w1_cnt < b1_cnt:
            rank_ops.append(
                _Action(stage_id_chunk1, computation_type=W, microbatch_index=w1_cnt)
            )
            w1_cnt += 1
        while w0_cnt < b0_cnt:
            rank_ops.append(
                _Action(stage_id_chunk0, computation_type=W, microbatch_index=w0_cnt)
            )
            w0_cnt += 1

        if not (w0_cnt == b0_cnt and b0_cnt == f0_cnt):
            raise AssertionError(
                f"Expected w0_cnt == b0_cnt == f0_cnt, got w0_cnt={w0_cnt}, b0_cnt={b0_cnt}, f0_cnt={f0_cnt}"
            )
        if not (w1_cnt == b1_cnt and b1_cnt == f1_cnt):
            raise AssertionError(
                f"Expected w1_cnt == b1_cnt == f1_cnt, got w1_cnt={w1_cnt}, b1_cnt={b1_cnt}, f1_cnt={f1_cnt}"
            )
        # We use max() in the n_micro computation above, so we may need to
        # remove redundant microbatches
        rank_ops = [
            (
                action
                if action is not None
                and action.microbatch_index is not None
                and action.microbatch_index < self._n_microbatches
                else None
            )
            for action in rank_ops
        ]
        return rank_ops