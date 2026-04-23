def state_dict(self) -> dict[str, Any]:
        r"""
        Return the last global optimizer state known to this rank.

        .. warning:
            If the state has not been consolidated to this rank, this raises a
            runtime error, and even if it has, the state may not be up-to-date,
            depending on when :meth:`consolidate_state_dict` was last called.

        Raises:
            RuntimeError: if ``overlap_with_ddp=True`` and this method is
                called before this :class:`ZeroRedundancyOptimizer` instance
                has been fully initialized, which happens once
                :class:`DistributedDataParallel` gradient buckets have been
                rebuilt; or if this method is called without a preceding call
                to :meth:`consolidate_state_dict`.
        """
        self._check_overlap_initialized()

        if len(self._all_state_dicts) == 0:
            raise RuntimeError(
                "Optimizer state has not been consolidated on this rank. "
                f"Please call `consolidate_state_dict(to={self.rank})` on "
                "all ranks beforehand if you meant to save the global state."
            )

        # Get the possibly-stale global optimizer state that uses global
        # parameter indexing
        state_dict = super().state_dict()

        # Update the global optimizer state with local state information,
        # factoring in the translation from local to global indexing
        for rank, local_state_dict in enumerate(self._all_state_dicts):
            local_param_groups = local_state_dict["param_groups"]
            global_param_groups = self._partition_parameters()[rank]
            if len(local_param_groups) != len(global_param_groups):
                raise AssertionError(
                    "Mismatch between number of local and global parameter groups"
                )

            for local_param_group, global_param_group in zip(
                local_param_groups, global_param_groups
            ):
                # `local_param_group` stores local indices, while
                # `global_param_group` stores the tensors directly
                local_param_indices = local_param_group["params"]
                global_params = global_param_group["params"]

                if len(local_param_indices) != len(global_params):
                    raise AssertionError(
                        "Mismatch between number of local and global "
                        "parameters in parameter group"
                    )
                for local_param_index, global_param in zip(
                    local_param_indices, global_params
                ):
                    # Update the global parameter state, if any
                    if local_param_index in local_state_dict["state"]:
                        global_param_index = self._param_to_index[global_param]
                        state_dict["state"][global_param_index] = local_state_dict[
                            "state"
                        ][local_param_index]

        # Sort the parameters in the state
        state_dict["state"] = dict(sorted(state_dict["state"].items()))
        return state_dict