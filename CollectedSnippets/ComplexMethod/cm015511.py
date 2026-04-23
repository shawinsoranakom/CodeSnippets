def test_save_and_load_after_forward_state_dict(
        self, state_dict_type, mixed_precision, state_dict_rank0_and_offload
    ):
        """
        Test that saving after some training results in params being updated as
        expected.
        """
        if state_dict_rank0_and_offload and state_dict_type != "state_dict":
            return
        torch.accelerator.set_device_index(self.rank)
        mixed_precision = (
            MixedPrecision(
                param_dtype=torch.float16,
                reduce_dtype=torch.float16,
                buffer_dtype=torch.float16,
            )
            if mixed_precision
            else None
        )
        model = self._get_simple_nested_model(mixed_precision=mixed_precision)
        optim = torch.optim.SGD(model.parameters(), lr=0.1)
        initial_params = get_full_params(model)
        for _ in range(6):
            inp = torch.randn(1, 10, device=torch.accelerator.current_device_index())
            output = model(*inp)
            loss = output.sum()
            expected_dtype = torch.float32 if mixed_precision is None else torch.float16
            self.assertEqual(expected_dtype, loss.dtype)
            loss.backward()
            optim.step()

        trained_params = get_full_params(model)
        # Ensure some training occurred
        self.assertNotEqual(initial_params, trained_params)
        # Save a copy of the state_dict
        fsd_mgr = self._get_state_dict_mgr(
            model, state_dict_type, state_dict_rank0_and_offload
        )
        with fsd_mgr:
            state_dict = model.state_dict()
            if state_dict_type == "state_dict":
                state_dict = {k: v.clone() for k, v in state_dict.items()}
            else:
                for sharded_tensor in state_dict.values():
                    shard = sharded_tensor._local_shards[0]
                    shard.tensor = shard.tensor.clone().detach_()
        self._validate_state_dict_contents(
            model, state_dict, state_dict_rank0_and_offload
        )
        _zero_model(model)

        # Ensure checkpointed params have the full param dtype
        for tensor in state_dict.values():
            self.assertEqual(tensor.dtype, torch.float32)

        # Load state_dict into zeroed model
        if state_dict_rank0_and_offload:
            state_dict = self._broadcast_state_dict(state_dict)

        with FSDP.state_dict_type(model, STATE_DICT_MAPPING[state_dict_type]):
            model.load_state_dict(state_dict, strict=True)
        loaded_params = get_full_params(model)
        self.assertEqual(loaded_params, trained_params)