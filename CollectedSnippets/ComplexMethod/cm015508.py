def test_state_dict_with_manual_ac_wrapper(
        self,
        state_dict_type: str,
        rank0_only_and_offload: bool,
    ):
        """
        Tests saving and loading a state dict for a model manually wrapped with
        ``FSDP(CheckpointWrapper(module))``, where the ``CheckpointWrapper`` is
        wrapped before FSDP.

        TODO: Investigate why the test above does not cover everything in this
        test and de-duplicate afterwards.
        """
        if state_dict_type == "sharded_state_dict" and rank0_only_and_offload:
            return  # not supported
        model_ac = TransformerWithSharedParams.init(
            self.process_group,
            FSDPInitMode.NO_FSDP,
            DEVICEInitMode.DEVICE_BEFORE,
        )
        # Manually wrap FSDP without AC
        model_no_ac = deepcopy(model_ac)
        for i, layer in enumerate(model_no_ac.transformer.encoder.layers):
            model_no_ac.transformer.encoder.layers[i] = FSDP(layer)
        for i, layer in enumerate(model_no_ac.transformer.decoder.layers):
            model_no_ac.transformer.decoder.layers[i] = FSDP(layer)
        model_no_ac.transformer = FSDP(model_no_ac.transformer)

        # Manually wrap FSDP with AC as `FSDP(CheckpointWrapper(module))`
        for i, layer in enumerate(model_ac.transformer.encoder.layers):
            layer = checkpoint_wrapper(layer)
            model_ac.transformer.encoder.layers[i] = FSDP(layer)
        for i, layer in enumerate(model_ac.transformer.decoder.layers):
            layer = checkpoint_wrapper(layer)
            model_ac.transformer.decoder.layers[i] = FSDP(layer)
        model_ac.transformer = FSDP(model_ac.transformer)

        # Save, load, and compare the two models
        with self._get_state_dict_mgr(
            model_no_ac, state_dict_type, rank0_only_and_offload
        ):
            state_dict_no_ac = model_no_ac.state_dict()
        with self._get_state_dict_mgr(
            model_ac, state_dict_type, rank0_only_and_offload
        ):
            state_dict_ac = model_ac.state_dict()
        self.assertEqual(state_dict_ac.keys(), state_dict_no_ac.keys())
        if rank0_only_and_offload:
            state_dict_no_ac = self._broadcast_state_dict(state_dict_no_ac)
            state_dict_ac = self._broadcast_state_dict(state_dict_ac)
        with self._get_state_dict_mgr(
            model_no_ac, state_dict_type, rank0_only_and_offload
        ):
            model_no_ac.load_state_dict(state_dict_no_ac)
        with self._get_state_dict_mgr(
            model_ac, state_dict_type, rank0_only_and_offload
        ):
            model_ac.load_state_dict(state_dict_ac)
        self._compare_models(model_ac, model_no_ac, self.assertEqual)