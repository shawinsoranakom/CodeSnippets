def _get_greedy_order_meta(self, sac_stats: SACStats) -> SACGreedyOrderMeta:
        # An inplace-op group is a set of inplace-ops that operate on the same underlying tensor storage.
        # 1. inplace_op_groups: A dictionary from the top-most parent of inplace-ops to the inplace-ops in the group
        #   The top-most op can itself be an inplace-op or can be a non-inplace op.
        # 2. inplace_op_to_group_head: A dictionary that maps all the inplace-ops to their respective group heads.
        inplace_op_groups: dict[int, set[int]] = {}
        inplace_op_to_group_head: dict[int, int] = dict(sac_stats.inplace_ops)

        # Initialize inplace_op_groups using inplace_op_to_group_head
        for op_idx, group_head_idx in inplace_op_to_group_head.items():
            op_group = inplace_op_groups.setdefault(group_head_idx, {group_head_idx})
            op_group.add(op_idx)

        # Like inplace ops, all of the random ops in the function/module should all be either recomputed or saved
        # as a group. This is because, they affect the ranom seed generator. If force_store_random is set True,
        # all of the random ops will be stored by default. For easy of manageability, we store the top-most random op
        # as the leader of the random_ops_group.
        random_ops_group: dict[int, set[int]] = {}
        random_group_head_idx = min(sac_stats.rand_ops, default=-1)
        has_rand_ops = bool(sac_stats.rand_ops)
        if has_rand_ops:
            random_ops_group[random_group_head_idx] = set(sac_stats.rand_ops)

        # 1. Random ops are stored if force_store_random is set
        # 2. View-like ops are recomputed by default
        # 3. For inplace_op_groups:
        #   a) If the head of this group is an inplace op, then we have to store the entire group.
        #   b) If any op in the group is random and force_store_random is set, then entire group will be stored.
        #   c) If none of ops in the group are random and the head of the group is not an in-place op, then
        #       this group can be considered for recomputation in its entirety
        stored_ops: set[int] = set()
        recomputed_ops: set[int] = set()
        # Case 1:
        if has_rand_ops and sac_stats.force_store_random:
            stored_ops.add(random_group_head_idx)
        # Case 2:
        recomputed_ops.update(set(sac_stats.view_like_ops))

        for group_head_idx, op_group in inplace_op_groups.items():
            # Case 3a:
            if group_head_idx in inplace_op_to_group_head:
                stored_ops.add(group_head_idx)
            # Case 3b:
            if (
                sac_stats.force_store_random & len(op_group & set(sac_stats.rand_ops))
                > 0
            ):
                stored_ops.add(group_head_idx)

        # The potential recompute candidates are populated as:
        recompute_candidates: set[int] = set()
        # 1) The random group head if it is not stored
        if has_rand_ops and random_group_head_idx not in stored_ops:
            recompute_candidates.add(random_group_head_idx)
        # 2) The in-place op group heads that are not stored
        recompute_candidates.update(set(inplace_op_groups.keys()) - stored_ops)
        # 3) The non-inplace and non-random ops that are neither stored nor recomputed by default
        recompute_candidates.update(
            set(range(len(sac_stats.memory)))
            - recomputed_ops
            - stored_ops
            - set(inplace_op_to_group_head.keys())
            - set(sac_stats.rand_ops)
        )

        # We define msps for a recomp candidate as the ratio of memory/runtime aka memory savings per second
        msps_meta: list[MSPS] = []
        for cand_idx in recompute_candidates:
            op_indices = {cand_idx}
            if cand_idx in inplace_op_groups:
                op_indices.update(inplace_op_groups[cand_idx])
            if has_rand_ops and cand_idx == random_group_head_idx:
                op_indices.update(sac_stats.rand_ops)

            mem = sum(sac_stats.memory[op_idx] for op_idx in op_indices)
            runtime = sum(sac_stats.runtimes[op_idx] for op_idx in op_indices)
            func_names = {sac_stats.func_names[op_idx] for op_idx in op_indices}
            msps = (mem / runtime) if runtime > 0 else sys.float_info.max
            msps_meta.append(MSPS(func_names, cand_idx, mem, runtime, msps))
        # We choose candidates to be recomputed based on increasing msps
        msps_meta.sort(key=lambda x: x.msps, reverse=True)
        return SACGreedyOrderMeta(
            recomputed_ops, stored_ops, inplace_op_groups, random_ops_group, msps_meta
        )