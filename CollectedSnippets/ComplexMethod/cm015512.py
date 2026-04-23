def test_state_dict_load_into_local_module(
        self,
        state_dict_type,
        state_dict_rank0_and_offload,
        fsdp_root,
    ):
        """
        Tests that FSDP's state_dict can be loaded into a local model.
        """
        if state_dict_rank0_and_offload and state_dict_type != "state_dict":
            return
        if not fsdp_root:
            model = self._get_non_fsdp_root_module()
        else:
            model = self._initialize_model(wrap_fsdp=True, register_buffers=True)
        optim = SGD(model.parameters(), lr=0.1)
        if not fsdp_root:
            in_data = torch.randn(
                1, 10, requires_grad=True, device=torch.device(device_type)
            )
        else:
            in_data = torch.rand(
                64, 4, requires_grad=True, device=torch.device(device_type)
            )
        for _ in range(3):
            out = model(in_data)
            out.sum().backward()
            optim.step()
            optim.zero_grad()

        with FSDP.summon_full_params(model):
            fsdp_params = deepcopy(list(model.parameters()))

        # get FSDP state_dict. Note that by default we return full_state_dict.
        sd_mgr = self._get_state_dict_mgr(
            model, state_dict_type, state_dict_rank0_and_offload
        )
        with sd_mgr:
            fsdp_state_dict = model.state_dict()

        ignore_keys = [k for k in fsdp_state_dict if NON_ROOT_FSDP_PREFIX in k]
        self._validate_state_dict_contents(
            model,
            fsdp_state_dict,
            state_dict_rank0_and_offload,
            ignore_keys=ignore_keys,
        )
        # Create zeroed local model
        if not fsdp_root:
            blank_local_model = self._get_non_fsdp_root_module(wrap=False)
        else:
            blank_local_model = self._initialize_model(
                wrap_fsdp=False, wrap_ddp=False, register_buffers=True
            )

        # Nothing should be FSDP
        for mod in blank_local_model.modules():
            self.assertFalse(isinstance(mod, FSDP))

        for param in blank_local_model.parameters():
            with torch.no_grad():
                param.zero_()

        fsdp_state_dict = _gather_state_dict(fsdp_state_dict)

        # Load fsdp's full state dict into the local and verify params are as
        # expected.
        if state_dict_rank0_and_offload:
            fsdp_state_dict = self._broadcast_state_dict(fsdp_state_dict)

        blank_local_model.load_state_dict(fsdp_state_dict, strict=True)
        local_params = list(blank_local_model.parameters())
        for fsdp_param, local_param in zip(fsdp_params, local_params):
            self.assertEqual(fsdp_param, local_param)