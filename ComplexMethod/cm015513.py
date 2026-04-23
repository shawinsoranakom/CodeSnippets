def test_state_dict_skip_module(self, state_dict_type, double_nest):
        torch.accelerator.set_device_index(self.rank)

        def _create_module(wrap_fsdp=True):
            LINEAR_SKIP = "linear_skip"
            ctx = enable_wrap(wrapper_cls=FSDP) if wrap_fsdp else nullcontext()
            with ctx:
                module = SkipModel(double_nest=double_nest)
                # Full name of linear_skip param tensors in SkipModel, as would be
                # stored in checkpoint.
                linear_skip_tensor_names = [
                    k for k in dict(module.named_parameters()) if LINEAR_SKIP in k
                ]
                # skip SkipModule
                linear_skip = getattr(module, LINEAR_SKIP)
                delattr(module, LINEAR_SKIP)
                # Wrap FSDP
                fsdp = wrap(module)
                # reattach
                setattr(module, LINEAR_SKIP, linear_skip)
                return fsdp, linear_skip_tensor_names

        fsdp, _ = _create_module()
        # Run a forward pass
        inp = torch.randn((1, 10), device=torch.accelerator.current_device_index())
        loss = fsdp(inp)
        loss.sum().backward()

        with FSDP.state_dict_type(fsdp, STATE_DICT_MAPPING[state_dict_type]):
            state_dict = fsdp.state_dict()
        if self.rank == 0 and state_dict_type != "local_state_dict":
            sd_keys = list(state_dict.keys())
            expected = list(SkipModel(double_nest=False).state_dict().keys())
            self.assertEqual(sorted(sd_keys), sorted(expected))
            # TODO: parameters in linear_skip_tensor_names should not be handled
            # by FSDP.state_dict(). Have a check once this is implemented in
            # FSDP.state_dict().

        # Check that it can be loaded into FSDP.
        new_fsdp, _ = _create_module()
        _zero_model(new_fsdp)
        for p1, p2 in zip(fsdp.parameters(), new_fsdp.parameters()):
            self.assertNotEqual(p1, p2)
        with FSDP.state_dict_type(new_fsdp, STATE_DICT_MAPPING[state_dict_type]):
            if state_dict_type != "local_state_dict":
                # FlatParameter has not supported deepcopy yet.
                state_dict = deepcopy(state_dict)
            new_fsdp.load_state_dict(state_dict, strict=True)
        for p1, p2 in zip(fsdp.parameters(), new_fsdp.parameters()):
            self.assertEqual(p1, p2)

        # Test that the checkpoint can be loaded into a local model.
        local, _ = _create_module(wrap_fsdp=False)
        for param in local.parameters():
            with torch.no_grad():
                param.zero_()

        with fsdp.summon_full_params(fsdp):
            for p1, p2 in zip(fsdp.parameters(), local.parameters()):
                self.assertNotEqual(p1, p2)

        if state_dict_type == "local_state_dict":
            return
        state_dict = _gather_state_dict(state_dict)
        with fsdp.summon_full_params(fsdp):
            if self.rank == 0:
                local.load_state_dict(state_dict, strict=True)
                for p1, p2 in zip(fsdp.parameters(), local.parameters()):
                    self.assertEqual(p1, p2)