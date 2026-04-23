def test_basic_save_and_load_state_dict(
        self,
        state_dict_type: str,
        cpu_offload: bool,
        fp16: bool,
        state_dict_rank0_and_offload: bool,
        use_orig_params: bool,
    ):
        """
        Tests that we can save a state_dict and load it into a blank model
        with various configs such as fp16 and cpu offload and parameters
        match as expected.
        """
        if (state_dict_rank0_and_offload and state_dict_type != "state_dict") or (
            use_orig_params and state_dict_type not in _UNFLATTENED_STATE_DICT_IMPLS
        ):
            return  # not supported
        device = torch.device(self.rank)
        for model_call in [
            partial(
                self._get_non_fsdp_root_module,
                cpu_offload=cpu_offload,
                use_orig_params=use_orig_params,
            ),
            partial(
                self._get_simple_nested_model,
                cpu_offload=cpu_offload,
                use_orig_params=use_orig_params,
            ),
            partial(
                self._get_simple_model,
                cpu_offload=cpu_offload,
                use_orig_params=use_orig_params,
            ),
        ]:
            model = model_call()
            if fp16:
                model.half()
            # Run a forward/backward to compute gradients to test the case
            # where there are gradients populated
            inp = torch.randn((3, 10), device=device)
            if fp16:
                inp = inp.half()
            model(inp).sum().backward()

            ctx = self._get_state_dict_mgr(
                model, state_dict_type, state_dict_rank0_and_offload
            )
            with ctx:
                fsdp_state_dict = _get_state_dict(
                    model, cpu_offload.offload_params, fp16
                )

            ignore_keys = [k for k in fsdp_state_dict if NON_ROOT_FSDP_PREFIX in k]

            self._validate_state_dict_contents(
                model,
                fsdp_state_dict,
                state_dict_rank0_and_offload,
                ignore_keys=ignore_keys,
            )
            if fp16:
                # Verify fp16 is the type
                for tensor in fsdp_state_dict.values():
                    self.assertEqual(tensor.dtype, torch.float16)

            model_new = model_call()
            if not cpu_offload.offload_params:
                model_new = model_new.to(device_type)
            if fp16:
                model_new.half()
            # Run a forward/backward to compute gradients to test the case
            # where there are gradients populated
            inp = torch.randn((3, 10), device=device)
            if fp16:
                inp = inp.half()
            model_new(inp).sum().backward()

            # zero the model to ensure parameters are different.
            _zero_model(model_new, zero_buffers=True)
            self._compare_models(model, model_new, self.assertNotEqual)

            # Verify parameters are the same in the new model.
            if state_dict_rank0_and_offload:
                fsdp_state_dict = self._broadcast_state_dict(fsdp_state_dict)
            with FSDP.state_dict_type(model_new, STATE_DICT_MAPPING[state_dict_type]):
                model_new.load_state_dict(fsdp_state_dict, strict=True)

            self._compare_models(model, model_new, self.assertEqual, check_fp16=fp16)