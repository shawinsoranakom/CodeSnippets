def _get_inplace_metadata(
        self, func: Any, out_storages: set[UntypedStorage]
    ) -> tuple[int, tuple[int, ...], dict[str, tuple[int, ...]]]:
        # 1. Get the current index of the metadata obtained so far
        curr_idx = len(self._sac_metadata)
        # 2. Get the set of active modules that are not leaf
        active_mod_fqns: set[str] = {
            par for par in self._mod_tracker.parents if par not in self._leaf_modules
        }
        # 3. Output ids are the identifies of the storage objects corresponding to the tensors
        output_ids = tuple(hash(st) for st in out_storages)
        # 4. If the function is not inplace, return
        if not is_inplace(func):
            return curr_idx, output_ids, dict.fromkeys(active_mod_fqns, ())

        op_idx = curr_idx
        # 5. Initialize the parent op ids of the inplace op for each of the active modules
        mod_op_parent_idxs: dict[str, int] = dict.fromkeys(active_mod_fqns, -1)
        for i, d in enumerate(self._sac_metadata):
            # 6. Find the first occurrence of a tensor corresponding to each module that
            # shares the same storage as the current tensor
            past_output_ids = d.output_ids
            if set(output_ids).issubset(set(past_output_ids)):
                for mod_fqn, op_parent_idx in mod_op_parent_idxs.items():
                    if op_parent_idx == -1:
                        if acm_stats := self._sac_mod_metadata.get(mod_fqn, None):
                            if i >= acm_stats.start_idx:
                                mod_op_parent_idxs[mod_fqn] = i
                        else:
                            if mod_fqn != "Global":
                                raise AssertionError
                            mod_op_parent_idxs[mod_fqn] = i
        # 7. If no parent tensor is found, then it's probably an inplace op on the arguments
        # so one can just store the current-op idx as parent idx
        for mod_fqn, op_parent_idx in mod_op_parent_idxs.items():
            if op_parent_idx < 0:
                mod_op_parent_idxs[mod_fqn] = op_idx
        mod_inplace_info = {
            mod_fqn: (op_idx, mod_op_parent_idxs[mod_fqn])
            for mod_fqn in active_mod_fqns
        }
        return curr_idx, output_ids, mod_inplace_info