def _get_sac_stats(
        self, data: list[_SACMetadata], force_store_random: bool
    ) -> SACStats:
        # 1. Ignore the operations that should be skipped by SAC such as aten.detach.default because autograd
        # inserts those during backward and it breaks the fwd-bwd alignment
        filtered_data = [x for x in data if x.func not in OPS_TO_ALWAYS_SKIP]

        (
            ops,
            runtimes_,
            memory_,
            new_ids,
            output_ids,
            inplace_ops_,
            view_like_ops_,
            rand_ops_,
        ) = zip(*[astuple(x) for x in filtered_data], strict=True)

        # 2. Extract the metadata information
        runtimes = list(runtimes_)
        memory = list(memory_)
        func_names = [op._overloadpacket.__name__ for op in ops]
        view_like_ops = [i for i, x in enumerate(view_like_ops_) if x]
        rand_ops = [i for i, x in enumerate(rand_ops_) if x]
        saved_autograd_ops = [
            i
            for i, out_ids in enumerate(output_ids)
            if set(out_ids).issubset(self._saved_tensor_ids)
        ]

        # 3. Remap the inplace indices as we have removed OPS_TO_ALWAYS_SKIP
        # FIXME @sanketpurandare: Fix this by changing the parent of the inplace-op
        # to itself if the original parent is in OPS_TO_ALWAYS_SKIP.
        try:
            inplace_ops = [tuple(map(new_ids.index, x)) for x in inplace_ops_ if x]
        except ValueError as err:
            raise ValueError(
                f"The remapping of inplace ops failed since one of the inplace op parents"
                f" must have been present in {OPS_TO_ALWAYS_SKIP}"
            ) from err

        # 4. The last operation is always stored as the output of the checkpoint
        # block, so we can avoid recomputing it. We set the memory to zero
        # instead of adding a new constraint because we want both the 0 and 1
        # endpoints for memory_budget to be valid
        # FIXME @sanketpurandare: this heuristic for finding the last non-view non-inplace op
        # might not always be correct, which would yield suboptimal policies
        last_op = len(ops) - 1
        skip_ops_ = set(view_like_ops) | set({x[0] for x in inplace_ops})
        reversed_skip_ops = sorted(skip_ops_, reverse=True)
        for op in reversed_skip_ops:
            if op == last_op:
                last_op -= 1

        memory[last_op] = 0

        # 5. Create a single ``SACStats`` object for the entire block of ``_SACMetadata``.
        return SACStats(
            func_names=func_names,
            runtimes=runtimes,
            memory=memory,
            view_like_ops=view_like_ops,
            rand_ops=rand_ops,
            saved_autograd_ops=saved_autograd_ops,
            inplace_ops=inplace_ops,  # type: ignore[arg-type]
            force_store_random=force_store_random,
        )