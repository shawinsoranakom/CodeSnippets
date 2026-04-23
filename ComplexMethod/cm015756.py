def check_step(self, data_list, data_with_config, defaults, norm_type="L1"):
        sparsifier = self._make_sparsifier(
            data_list,
            data_with_config,
            defaults,
            sparsifier_type=DataNormSparsifier,
            sparsifier_kwargs={"norm": norm_type},
        )
        all_data = data_list + data_with_config

        # mask before step() should not be sparsified
        for some_data in all_data:
            name, _, _ = self._get_name_data_config(some_data)
            mask = sparsifier.get_mask(name=name)
            if (1.0 - mask.mean()) != 0:
                raise AssertionError("Expected sparsity level to be 0 before step")

        sparsifier.step()

        for some_data in all_data:
            name, _, _ = self._get_name_data_config(some_data)
            mask = sparsifier.get_mask(name=name)
            config = sparsifier.data_groups[name]
            lb, ub = self._get_bounds_on_actual_sparsity(config, mask.shape)
            mask = mask.to(torch.float)
            actual_sparsity = round(1 - mask.mean().item(), 3)
            if not (actual_sparsity >= lb and actual_sparsity <= ub):
                raise AssertionError(
                    f"Actual sparsity {actual_sparsity} not in bounds [{lb}, {ub}]"
                )
            if actual_sparsity <= 0.0:
                raise AssertionError("Actual sparsity should be > 0.0")

        iters_before_collapse = 100

        test_sparsifier = DataNormSparsifier(
            sparsity_level=0.5,
            sparse_block_shape=(1, 4),
            zeros_per_block=4,
            norm=norm_type,
        )

        for _ in range(iters_before_collapse):
            new_data = torch.randn(20, 20)
            test_sparsifier.add_data(name="test_data", data=new_data)
            test_sparsifier.step()
            mask = test_sparsifier.get_mask(name="test_data")
            mask = mask.to(torch.float)
            if (1.0 - mask.mean().item()) <= 0:
                raise AssertionError("Expected some sparsity to be achieved")