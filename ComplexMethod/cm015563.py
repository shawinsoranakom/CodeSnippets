def _test_save_load(
        self,
        init_model_optim: Callable,
        test_frozen: bool = False,
        flatten_optimizer: bool = False,
    ) -> None:
        options = StateDictOptions(
            ignore_frozen_params=test_frozen,
            flatten_optimizer_state_dict=flatten_optimizer,
        )
        # Initialize original model and distributed model.
        model, optim, copy_optim, dist_model, dist_optim = init_model_optim()

        # Train 10 steps.
        _dist_optim = [dist_optim] if not isinstance(dist_optim, list) else dist_optim
        for _ in range(10):
            optim.zero_grad()
            for d_optim in _dist_optim:
                d_optim.zero_grad()

            batch = torch.rand(8, 100, device=device_type)
            model(batch).sum().backward()
            dist_model(batch).sum().backward()

            optim.step()
            for d_optim in _dist_optim:
                d_optim.step()

        # We need to ensure gradients don't exist, this the invariant of using DSD.
        optim.zero_grad()

        # Get the state_dict, and compare the result
        msd = model.state_dict()
        osd = optim.state_dict()
        dist_msd, dist_osd = get_state_dict(
            dist_model, optimizers=dist_optim, options=options
        )
        self._verify_msd(msd, dist_msd, options)
        self._verify_osd_by_load(model, optim, copy_optim, dist_osd)
        if not flatten_optimizer:
            self._verify_osd(model, optim, osd, dist_osd)

        # Initialize a completely new model to simulate checkpoint load.
        _, _, _, dist_model, dist_optim = init_model_optim()

        # Simulate DCP distributed load. We need to first get the state_dict and
        # pass them to DCP to load the saved state_dict from the storage.
        # Then finally we can call set_state_dict().
        if not isinstance(dist_optim, list):
            dist_optim = [dist_optim]
        if test_frozen:
            # We won't be able to load the partial state_dict back.
            return
        # Since we already have the state_dict saved before, no need to call DCP.
        # We can directly load them back. This assert is to ensure that optimizer
        # state storage are initialized.
        # self.assertEqual(len(curr_dist_osd[STATE]), len(dist_osd[STATE]))
        set_model_state_dict(
            dist_model,
            model_state_dict=dist_msd,
            options=options,
        )
        set_optimizer_state_dict(
            dist_model,
            optimizers=dist_optim,
            optim_state_dict=dist_osd,
            options=options,
        )

        # Check if the new state_dict are the same
        dist_msd, dist_osd = get_state_dict(
            dist_model, optimizers=dist_optim, options=options
        )
        self._verify_msd(msd, dist_msd, options)
        # TODO: Ditto
        # self._verify_osd_by_load(model, optim, copy_optim, dist_osd)
        if not flatten_optimizer:
            self._verify_osd(model, optim, osd, dist_osd)

        # Test _patch_model_state_dict, and _patch_optimizer_state_dict
        _patch_model_state_dict(dist_model, options=options)
        _patch_optimizer_state_dict(dist_model, optimizers=dist_optim, options=options)
        dist_msd = dist_model.state_dict()
        dist_osd = dist_optim[0].state_dict()
        self._verify_msd(msd, dist_msd, options)
        self._verify_osd_by_load(model, optim, copy_optim, dist_osd)
        if not flatten_optimizer:
            self._verify_osd(model, optim, osd, dist_osd)