def init_cooperative_reduction(self):
        """One time setup code for cooperative reductions."""
        assert self.cooperative_reduction

        # shift all the grids over since tl.program_id(0) is for rsplit
        for tree in self.range_trees:
            if tree.grid_dim is not None:
                tree.grid_dim += 1

        sem_count = self.numels["x"]
        if self.fixed_config:
            sem_count = CeilDiv(sem_count, self.fixed_config["XBLOCK"])
        self.semaphores_name = self.args.semaphores(sem_count)
        self.cooperative_reduction_workspace_cache = CooperativeReductionWorkspaceCache(
            self.args
        )
        self.body.splice(
            """\
            RSPLIT_NEXT_POWER_OF_2: tl.constexpr = triton_helpers.constexpr_next_power_of_2(RSPLIT)
            RSPLIT_IS_POWER_OF_2: tl.constexpr = RSPLIT == RSPLIT_NEXT_POWER_OF_2
            HAS_RSPLIT: tl.constexpr = RSPLIT > 1
            rsplit_id = tl.program_id(0)
            num_rblocks = (rnumel + RBLOCK - 1) // RBLOCK
            rsplit_chunk = (num_rblocks + RSPLIT - 1) // RSPLIT * RBLOCK
            rsplit_start = rsplit_chunk * rsplit_id
            rsplit_end = rsplit_chunk * (rsplit_id + 1)
            """,
        )
        if any(
            not self._has_constant_mask(tree)
            for tree in self.range_trees
            if tree.is_reduction
        ):
            self.body.writeline(
                "rsplit_end = tl.where(rsplit_end < rnumel, rsplit_end, rnumel)"
            )