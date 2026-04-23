def _test_shard_full_optim_state_dict_unmanaged_params(
        self,
        state_dict_type: StateDictType,
        add_to_fsdp_module: bool,
        use_optim_input: bool,
    ):
        NUM_ITERS = 1
        # Create a normal wrapped model
        model, optim, optim_input = self._init_nested_model(wrap=True)
        self._step_model(model, optim, num_iters=NUM_ITERS)

        if state_dict_type == StateDictType.FULL_STATE_DICT:
            fsdp_osd = (
                FSDP.full_optim_state_dict(model, optim, optim_input, rank0_only=False)
                if use_optim_input
                else FSDP.full_optim_state_dict(model, optim, rank0_only=False)
            )  # save on all ranks to avoid having to broadcast from rank 0
        else:
            fsdp_osd = FSDP.sharded_optim_state_dict(model, optim)
        # Create a new model with the same structure but additional unmanaged
        # parameters, representing the model for which we want to load
        device = torch.device("cuda")
        model = NestedModel().to(device)
        model, unmanaged_params = NestedModel.wrap_with_unmanaged_params(
            model,
            add_to_fsdp_module,
        )
        optim_input = list(model.parameters())
        optim = torch.optim.Adam(optim_input, lr=1e-3)
        if add_to_fsdp_module:
            # If we add the unmanaged parameters to a module wrapped with FSDP,
            # then the flat parameter will be comprised of some unflattened
            # parameters with zero-dimensional tensor state (i.e. Adam "step")
            # and others without (i.e. the unmanaged parameters), which
            # triggers an error that we have to ensure correctness
            error_prefix = (
                "^(All unflattened parameters comprising a "
                "single flat parameter must have scalar state with the "
                "same value and dtype)"
            )
            with self.assertRaisesRegex(ValueError, error_prefix):
                if state_dict_type == StateDictType.FULL_STATE_DICT:
                    (
                        FSDP.shard_full_optim_state_dict(
                            fsdp_osd, model, optim_input=optim_input
                        )
                        if use_optim_input
                        else FSDP.shard_full_optim_state_dict(
                            fsdp_osd, model, optim=optim
                        )
                    )
                else:
                    FSDP.flatten_sharded_optim_state_dict(fsdp_osd, model, optim=optim)
        else:
            # If we add the unmanaged parameters to a module not wrapped with
            # FSDP, then we simply ignore them without erroring to enable
            # model parallelism use cases, where some parameters are managed
            # externally to FSDP
            if state_dict_type == StateDictType.FULL_STATE_DICT:
                flattened_osd = (
                    FSDP.shard_full_optim_state_dict(
                        fsdp_osd, model, optim_input=optim_input
                    )
                    if use_optim_input
                    else FSDP.shard_full_optim_state_dict(fsdp_osd, model, optim=optim)
                )
            else:
                flattened_osd = FSDP.flatten_sharded_optim_state_dict(
                    fsdp_osd, model, optim=optim
                )
            # Add entries for the unmanaged parameters to be able to load
            for unmanaged_param in unmanaged_params:
                NestedModel.add_unmanaged_param_entry(
                    flattened_osd,
                    unmanaged_param,
                    NUM_ITERS,
                )
            # Check that we can load the optimizer state dict
            optim.load_state_dict(flattened_osd)