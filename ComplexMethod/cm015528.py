def _test_load_optim_state(
        self,
        model_class: _ModelClass,
        use_multiple_param_groups: bool,
        halve_world_size: bool,
        osd_comm_method: _OSDCommMethod,
        use_diff_optim_inputs: bool,
        use_optim_input: bool,
        num_iters: int,
        **new_model_kwargs,
    ):
        """
        (1) Runs a model with full world size for K iterations to generate a
        full/sharded optimizer state dict;
        (2) initializes a model with halved world size and possibly different
        FSDP wrapping scheme (based on ``new_model_kwargs``);
        (3) loads the full/sharded optimizer state dict from (1) according to the
        halved-world-size model;
        (4) runs the halved-world-size model for K iterations; and
        (5) checks that the sharded optimizer state dict from (3) matches the
        halved-world-size model's local optimizer state dict, meaning that the
        former could have equivalently been loaded into the local optimizer.
        """
        initializer = self._model_class[model_class]
        if osd_comm_method == _OSDCommMethod.OPTIM_STATE_DICT:
            osd_method = FSDP.optim_state_dict
        elif osd_comm_method == _OSDCommMethod.FLATTEN_SHARDED_OSD:
            osd_method = FSDP.sharded_optim_state_dict
        else:
            osd_method = FSDP.full_optim_state_dict

        # First, run a wrapped model with full world size for a few iterations
        model1, optim1, optim_input1 = initializer(
            wrap=True,
            use_multiple_param_groups=use_multiple_param_groups,
        )
        self._step_model(model1, optim1, num_iters=num_iters)
        fsdp_osd1 = (
            osd_method(model1, optim1, optim_input1)
            if use_optim_input
            else osd_method(model1, optim1)
        )
        if halve_world_size:
            # Create a new process group with halved world size
            new_group_ranks = [r for r in range(self.world_size) if r % 2 == 0]
            new_group = dist.new_group(ranks=new_group_ranks)
            if self.rank not in new_group_ranks:
                return
        else:
            # Continue using the same group and hence world size
            new_group = dist.distributed_c10d._get_default_group()
        # Second, run a wrapped model with (possibly) halved world size and
        # (possibly) differing `optim_input` across ranks
        model2, optim2, optim_input2 = initializer(
            wrap=True,
            group=new_group,
            use_multiple_param_groups=use_multiple_param_groups,
            use_diff_optim_inputs=use_diff_optim_inputs,
            **new_model_kwargs,  # specify `wrap_alt` to change wrapping
        )
        self._step_model(model2, optim2, num_iters=num_iters)
        fsdp_osd2 = (
            osd_method(model2, optim2, optim_input2, group=new_group)
            if use_optim_input
            else osd_method(model2, optim2, group=new_group)
        )
        # Compute two sharded optim state dicts: (1) for the first model
        # according to the second model and (2) for the second model according
        # to the second model
        if osd_comm_method == _OSDCommMethod.BROADCAST_OBJECT_LIST:
            fsdp_osd1 = self._broadcast_full_osd(fsdp_osd1, group=new_group)
            sharded_osd1 = (
                FSDP.shard_full_optim_state_dict(
                    fsdp_osd1, model2, optim_input=optim_input2
                )
                if use_optim_input
                else FSDP.shard_full_optim_state_dict(fsdp_osd1, model2, optim=optim2)
            )
            fsdp_osd2 = self._broadcast_full_osd(fsdp_osd2, group=new_group)
            sharded_osd2 = (
                FSDP.shard_full_optim_state_dict(
                    fsdp_osd2, model2, optim_input=optim_input2
                )
                if use_optim_input
                else FSDP.shard_full_optim_state_dict(fsdp_osd2, model2, optim=optim2)
            )
        elif osd_comm_method == _OSDCommMethod.SCATTER_FULL_OSD:
            sharded_osd1 = (
                FSDP.scatter_full_optim_state_dict(
                    fsdp_osd1 if self.rank == 0 else None,
                    model2,
                    optim_input=optim_input2,
                    group=new_group,
                )
                if use_optim_input
                else FSDP.scatter_full_optim_state_dict(
                    fsdp_osd1 if self.rank == 0 else None,
                    model2,
                    optim=optim2,
                    group=new_group,
                )
            )
            sharded_osd2 = (
                FSDP.scatter_full_optim_state_dict(
                    fsdp_osd2 if self.rank == 0 else None,
                    model2,
                    optim_input=optim_input2,
                    group=new_group,
                )
                if use_optim_input
                else FSDP.scatter_full_optim_state_dict(
                    fsdp_osd2 if self.rank == 0 else None,
                    model2,
                    optim=optim2,
                    group=new_group,
                )
            )
        elif osd_comm_method == _OSDCommMethod.FLATTEN_SHARDED_OSD:
            sharded_osd1 = FSDP.flatten_sharded_optim_state_dict(
                fsdp_osd1,
                model2,
                optim=optim2,
            )
            sharded_osd2 = FSDP.flatten_sharded_optim_state_dict(
                fsdp_osd2,
                model2,
                optim=optim2,
            )
        elif osd_comm_method == _OSDCommMethod.OPTIM_STATE_DICT:
            sharded_osd1 = FSDP.optim_state_dict_to_load(model2, optim2, fsdp_osd1)
            sharded_osd2 = FSDP.optim_state_dict_to_load(model2, optim2, fsdp_osd2)

        # As a sanity check, check that sharding the second model's full/sharded
        # optimizer state dict according to itself is equivalent to its local
        # optimizer's state dict
        local_osd2 = optim2.state_dict()
        check_same_param_keys = True  # should all have matching parameter IDs
        self._check_same_param_groups(
            sharded_osd2,
            local_osd2,
            check_same_param_keys=check_same_param_keys,
        )
        self._check_same_state(
            sharded_osd2,
            local_osd2,
            check_same_param_keys=check_same_param_keys,
        )
        # Check that sharding the first model's full/sharded optimizer state dict
        # according to the second model is equivalent to the second model's
        # local optimizer state dict
        self._check_same_param_groups(
            sharded_osd1,
            local_osd2,
            check_same_param_keys=check_same_param_keys,
        )
        self._check_same_state(
            sharded_osd1,
            local_osd2,
            check_same_param_keys=check_same_param_keys,
        )
        # As a sanity check, check that we can load and run a few iterations
        optim2.load_state_dict(sharded_osd2)
        self._step_model(model2, optim2, num_iters=num_iters)