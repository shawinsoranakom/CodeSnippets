def _check_same_state(
        self,
        fsdp_osd,
        ref_osd,
        check_same_param_keys: bool,
    ):
        """Checks that ``full_osd`` and ``ref_osd`` have the same "state" part.
        If ``check_same_param_keys=True``, then checks that the parameter keys
        match (e.g. when both should be parameter names), and does not check
        the parameter keys otherwise."""
        if "state" not in ref_osd:
            raise AssertionError("Expected 'state' in ref_osd")
        self.assertTrue("state" in fsdp_osd)
        ref_osd_state = ref_osd["state"]
        fsdp_osd_state = {
            k: _gather_state_dict(v) for k, v in fsdp_osd["state"].items()
        }

        if check_same_param_keys:
            # Check parameter keys are the same first for earlier erroring
            ref_osd_param_ids = set(ref_osd_state.keys())
            fsdp_osd_param_ids = set(fsdp_osd_state.keys())
            self.assertTrue(
                ref_osd_param_ids == fsdp_osd_param_ids,
                f"Rank {self.rank}: {(ref_osd_param_ids, fsdp_osd_param_ids)}",
            )
            # Check state values are the same
            for param_id, param_state in fsdp_osd_state.items():
                for state_name, value in param_state.items():
                    ref_value = ref_osd_state[param_id][state_name]
                    self.assertEqual(value, ref_value)
            return
        # Otherwise, only require the parameter keys to be isomorphic (e.g.
        # between IDs and names)
        ref_osd_states = list(ref_osd_state.values())
        fsdp_osd_states = list(fsdp_osd_state.values())
        self.assertEqual(len(ref_osd_states), len(fsdp_osd_states))
        # Use brute-force quadratic-time comparison since it is hard to
        # hash a tensor by value instead of by object
        for fsdp_osd_state in fsdp_osd_states:
            # Check for at least one match (may be > 1 in toy edge cases, e.g.
            # multiple biases); nonetheless, each having >= 1 match and the two
            # lists having equal length imply that the list contents are equal
            self.assertTrue(
                any(
                    self._are_equal_states(fsdp_osd_state, ref_osd_state)
                    for ref_osd_state in ref_osd_states
                )
            )