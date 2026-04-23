def test_local_state_dict_reshard(self):
        """
        This test demonstrates the ability to do resharding when using
        local_state_dict. Although we do not recommend users to use
        local_state_dict, there are still some corner cases that
        using local_state_dict is a better solution.
        """
        model = FSDP(Model(wrap_fsdp=True)).to(device_type)
        optim = torch.optim.SGD(model.parameters(), lr=0.1)

        batch = torch.randn(4, 4, device=torch.accelerator.current_device_index())
        output = model(batch)
        loss = output.sum()
        loss.backward()
        optim.step()
        with FSDP.state_dict_type(model, StateDictType.LOCAL_STATE_DICT):
            state_dict = model.state_dict()

        rank = dist.get_rank()
        new_pg = dist.new_group(ranks=[0, 1])
        resharded_state_dict = {}
        # Mimic resharding from 4 GPUs to 2 GPUs
        for key, value in state_dict.items():
            if isinstance(value, ShardedTensor):
                full_flat_param = _all_gather_sharded_tensor(value)
                if rank < 2:
                    full_numel = full_flat_param.size()
                    chunks = full_flat_param.chunk(2)
                    flat_param = chunks[rank]
                    shard_offset = 0 if rank == 0 else chunks[0].numel()
                    local_shards = [
                        Shard.from_tensor_and_offsets(flat_param, [shard_offset], rank)
                    ]
                    sharded_tensor = init_from_local_shards(
                        local_shards, full_numel, process_group=new_pg
                    )
                    resharded_state_dict[key] = sharded_tensor
            else:
                if rank < 2:
                    resharded_state_dict[key] = value

        if rank < 2:
            model2 = FSDP(
                Model(wrap_fsdp=True, process_group=new_pg), process_group=new_pg
            ).to(device_type)
            with FSDP.state_dict_type(model2, StateDictType.LOCAL_STATE_DICT):
                model2.load_state_dict(resharded_state_dict)

        with FSDP.state_dict_type(model, StateDictType.FULL_STATE_DICT):
            full_state_dict1 = model.state_dict()

        if rank < 2:
            with FSDP.state_dict_type(model2, StateDictType.FULL_STATE_DICT):
                full_state_dict2 = model2.state_dict()
            self.assertEqual(full_state_dict1, full_state_dict2)