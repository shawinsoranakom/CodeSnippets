def _backward_prefetch(self) -> None:
        if self._training_state == TrainingState.PRE_BACKWARD:
            if not self._post_forward_indices:
                # Can be cleared if running multiple `backward`s
                return
            curr_index = self._post_forward_indices.pop()
            if self._num_param_groups > 1:
                # Backward fires groups in reverse forward order:
                # N-1, N-2, ..., 1, 0.  Index 1 is always the
                # penultimate group regardless of N.  Prefetching here
                # lets the next module's AG overlap with group 0's RS
                # without holding unsharded params too long (as would
                # happen if we prefetched from N-1).
                if self._param_group_index != 1:
                    return
                # E.g. fully_shard(block, shard_placement_fn=...) creates two
                # param groups per block (dense + moe), giving
                # post_forward_order = [block0, block0.moe, block1, block1.moe].
                # block1.moe walks back past block1 to prefetch block0.moe then block0.
                curr_modules = self.modules
                target_modules: tuple[nn.Module, ...] | None = None
                for step in range(1, curr_index + 1):
                    target = self.comm_ctx.post_forward_order[curr_index - step]
                    if target.modules is curr_modules:
                        continue
                    if target_modules is None:
                        target_modules = target.modules
                    elif target.modules is not target_modules:
                        break
                    # Prefetch all groups of the target module in
                    # reverse forward order (highest index first),
                    # matching the explicit path in _pre_backward.
                    self._prefetch_unshard(target, "backward")
            elif curr_index > 0:
                target = self.comm_ctx.post_forward_order[curr_index - 1]
                self._prefetch_unshard(target, "backward")