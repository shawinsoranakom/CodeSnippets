def test_interface_arguments(self):
        model = FSDP(TestDummyModel().cuda())
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)

        def step():
            loss = model(model.get_input())
            loss.backward(loss)
            optim.step()

        step()
        original_osd = deepcopy(optim.state_dict())
        osd = FSDP.optim_state_dict(model, optim, optim_state_dict=original_osd)
        self._check_same_state(
            FSDP.optim_state_dict(model, optim), osd, check_same_param_keys=True
        )
        step()

        FSDP.optim_state_dict_to_load(model, optim, osd, load_directly=True)
        self._check_same_state(
            optim.state_dict(), original_osd, check_same_param_keys=True
        )

        # Test the default setting.
        osd = FSDP.optim_state_dict(model, optim, optim_state_dict=original_osd)
        for state in osd["state"].values():
            for s in state.values():
                self.assertFalse(isinstance(s, ShardedTensor))
                self.assertFalse(s.is_cuda)

        # Test sharded state_dict without offload_to_cpu
        with FSDP.state_dict_type(
            model,
            StateDictType.SHARDED_STATE_DICT,
            ShardedStateDictConfig(),
            ShardedOptimStateDictConfig(offload_to_cpu=False),
        ):
            osd = FSDP.optim_state_dict(model, optim, optim_state_dict=original_osd)
            for state in osd["state"].values():
                for s in state.values():
                    if s.dim() == 0:
                        continue
                    self.assertTrue(isinstance(s, ShardedTensor))
                    if s._local_shards[0]:
                        self.assertTrue(s._local_shards[0].tensor.is_cuda)

        # Test full state_dict with rank0_only
        with FSDP.state_dict_type(
            model,
            StateDictType.FULL_STATE_DICT,
            FullStateDictConfig(),
            FullOptimStateDictConfig(
                offload_to_cpu=True,
                rank0_only=True,
            ),
        ):
            osd = FSDP.optim_state_dict(model, optim, optim_state_dict=original_osd)
            if dist.get_rank() > 0:
                self.assertEqual(osd, {})
            else:
                for state in osd["state"].values():
                    for s in state.values():
                        if s.dim() == 0:
                            continue
                        self.assertFalse(s.is_cuda)
                        self.assertFalse(isinstance(s, ShardedTensor))