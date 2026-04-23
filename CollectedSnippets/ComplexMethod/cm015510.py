def test_buffers_save_and_load_state_dict(
        self,
        state_dict_type: str,
        cpu_offload: bool,
        mixed_precision: bool,
        state_dict_rank0_and_offload: bool,
        use_orig_params: bool,
    ):
        """
        Tests that we can save a state_dict and load it for modules with persistent buffers, including
        in the context of non-default mixed precision, different ``state_dict_type`` s and CPU offloading.
        """
        if (state_dict_rank0_and_offload and state_dict_type != "state_dict") or (
            use_orig_params and state_dict_type not in _UNFLATTENED_STATE_DICT_IMPLS
        ):
            return  # not supported
        mixed_precision = (
            MixedPrecision(
                param_dtype=torch.float16,
                reduce_dtype=torch.float16,
                buffer_dtype=torch.float16,
            )
            if mixed_precision
            else None
        )
        model_call = partial(
            self._get_multibuffer_nested_model,
            cpu_offload=cpu_offload,
            use_orig_params=use_orig_params,
            mixed_precision=mixed_precision,
        )
        model = model_call()
        ctx = self._get_state_dict_mgr(
            model, state_dict_type, state_dict_rank0_and_offload
        )
        with ctx:
            fsdp_state_dict = _get_state_dict(model, cpu_offload.offload_params, False)

        self._validate_state_dict_contents(
            model, fsdp_state_dict, state_dict_rank0_and_offload
        )

        model_new = model_call()
        if not cpu_offload.offload_params:
            model_new = model_new.to(device_type)

        # zero the model to ensure parameters are different.
        _zero_model(model_new, zero_buffers=True)
        self._compare_models(model, model_new, self.assertNotEqual)

        # Verify parameters are the same in the new model.
        if state_dict_rank0_and_offload:
            fsdp_state_dict = self._broadcast_state_dict(fsdp_state_dict)
        with FSDP.state_dict_type(model_new, STATE_DICT_MAPPING[state_dict_type]):
            model_new.load_state_dict(fsdp_state_dict, strict=True)

        self._compare_models(model, model_new, self.assertEqual)