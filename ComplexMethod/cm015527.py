def _test_optim_state_dict_nested(
        self,
        state_dict_type: StateDictType,
        use_multiple_param_groups: bool,
        rank0_only: bool,
        use_diff_optim_inputs: bool,
        use_optim_input: bool,
    ) -> None:
        if rank0_only and state_dict_type == StateDictType.SHARDED_STATE_DICT:
            return  # not supported
        NUM_ITERS = 3
        model1, optim1, optim_input = self._init_nested_model(
            wrap=True,
            use_multiple_param_groups=use_multiple_param_groups,
            use_diff_optim_inputs=use_diff_optim_inputs,
        )
        losses1 = self._step_model(model1, optim1, num_iters=NUM_ITERS)
        if state_dict_type == StateDictType.FULL_STATE_DICT:
            if use_optim_input:
                fsdp_osd = FSDP.full_optim_state_dict(
                    model1,
                    optim1,
                    optim_input,
                    rank0_only=rank0_only,
                )
            else:
                fsdp_osd = FSDP.full_optim_state_dict(
                    model1,
                    optim1,
                    rank0_only=rank0_only,
                )
        else:
            fsdp_osd = FSDP.sharded_optim_state_dict(model1, optim1)
        # Non-target ranks get an empty state dict
        if rank0_only and self.rank != 0:
            self.assertEqual(len(fsdp_osd), 0)
            return
        model2, optim2, _ = self._init_nested_model(
            wrap=False,
            use_multiple_param_groups=use_multiple_param_groups,
            use_diff_optim_inputs=use_diff_optim_inputs,
        )
        losses2 = self._step_model(model2, optim2, num_iters=NUM_ITERS)
        ref_osd = optim2.state_dict()
        # Check the losses to eliminate model drift as a source of error
        for i, (l1, l2) in enumerate(zip(losses1, losses2)):
            if l1 != l2:
                raise AssertionError(f"Losses differ on iter {i}: {l1:.5f} {l2:.5f}")
        # Do not check the parameter keys since the full/sharded optimizer state
        # dict uses parameter names, while the non-wrapped equivalent uses
        # parameter IDs
        check_same_param_keys = False
        self._check_same_param_groups(
            fsdp_osd,
            ref_osd,
            check_same_param_keys=check_same_param_keys,
        )
        self._check_same_state(
            fsdp_osd,
            ref_osd,
            check_same_param_keys=check_same_param_keys,
        )