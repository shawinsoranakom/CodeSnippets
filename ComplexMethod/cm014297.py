def check_recomputed_tensors_match(self, gid) -> None:
        if self.ignore_saved_mismatch:
            # TODO: we can probably make this check stricter by checking that
            #       the metadata of the first tensors still match.
            return
        # NOTE [ Error handling for checkpoint ]
        #
        # At a high level, we need to check that the tensors saved
        # during original forward matches tensors saved during recompute
        # This means handling 3 cases:
        #
        # 1. During recompute, more tensors were saved.
        #
        #    Usually this is hidden due to the StopRecomputationError
        #    but if early stop is not enabled, or we would have errored
        #    anyway because there aren't enough weak_holders. But we
        #    do want to have a nice error. See the _recomputation_hook
        #    for details.
        if not len(self.weak_holders) == self.recomp_counter[gid]:
            # 2. During recompute, fewer tensors were saved
            #
            # We know that every time we save something do original forward
            # we append to weak_holder, and every time we save a tensor
            # during recompute we increment recompute_counter.
            raise CheckpointError(
                "torch.utils.checkpoint: A different number of tensors was saved "
                "during the original forward and recomputation.\n"
                f"Number of tensors saved during forward: {len(self.weak_holders)}\n"
                f"Number of tensors saved during recomputation: {self.recomp_counter[gid]}.\n"
                f"{_debug_tip_msg}"
            )

        # 3. During recompute, the same tensors were saved, but they
        #    have different metadata
        nb_meta_different = []
        for idx, weak_holder in enumerate(self.weak_holders):
            holder = weak_holder()
            if holder is None:
                continue
            # We've seen all holders since we iterate over them in order
            # For every holder that is still alive now, it must've been
            # alive when we saw it during recompute, therefore, the
            # gid must be set.
            _internal_assert(gid in holder.handles)
            # We know this is the first unpack, so it couldn't have been set
            # to None yet.
            _internal_assert(holder.handles[gid] is not None)
            # We always set these together in the recomputation hook
            _internal_assert(holder.handles[gid] in self.recomputed[gid])
            # see pack hook, x_metadata is 1:1 with weak_holders.
            x_meta = self.x_metadatas[idx]
            recomputed_x = self.recomputed[gid][holder.handles[gid]]
            if x_meta != self.metadata_fn(recomputed_x):
                nb_meta_different.append((idx, x_meta, self.metadata_fn(recomputed_x)))

        if len(nb_meta_different) > 0:
            mismatched_tensors = ""
            for idx, x_meta, recomputed_meta in nb_meta_different:
                mismatched_tensors += (
                    f"tensor at position {idx}:\n"
                    f"saved metadata: {x_meta}\n"
                    f"recomputed metadata: {recomputed_meta}\n"
                )
            raise CheckpointError(
                "torch.utils.checkpoint: Recomputed values for the following tensors "
                "have different metadata than during the forward pass.\n"
                f"{mismatched_tensors}.\n"
                f"{_debug_tip_msg}"
            )