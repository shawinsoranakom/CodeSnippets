def check_sparsity_level(
        self, data_list, data_with_config, defaults, norm_type="L1"
    ):
        sparsity_levels = [-1.0, 0.0, 0.5, 1.0, 2.0]
        sparse_block_shapes = [(1, 1), (1, 4), (2, 2), (4, 1)]
        zeros_per_blocks = [0, 1, 2, 3, 4]
        sparsifier = DataNormSparsifier(data_list=data_list, norm=norm_type)

        testcases = itertools.tee(
            itertools.product(sparsity_levels, sparse_block_shapes, zeros_per_blocks)
        )

        if not (
            len(data_with_config) > 0
            and "name" in data_with_config[0]
            and "data" in data_with_config[0]
        ):
            raise AssertionError(
                "data_with_config must have at least one entry with 'name' and 'data'"
            )
        # get some data
        name, data = data_with_config[0]["name"], data_with_config[0]["data"]
        for idx, (sl, sbs, zpb) in enumerate(testcases[0]):
            new_name = f"{name}_{idx}"
            if zpb > sbs[0] * sbs[1]:
                continue
            current_config = {
                "sparsity_level": sl,
                "sparse_block_shape": sbs,
                "zeros_per_block": zpb,
            }
            sparsifier.add_data(name=new_name, data=data, **current_config)
            if zpb > sbs[0] * sbs[1]:
                continue

        sparsifier.step()
        sparsifier.squash_mask()
        for idx, (sl, sbs, zpb) in enumerate(testcases[0]):
            new_name = f"{name}_{idx}"
            sparsified_data = sparsifier.get_data(name=new_name, original=False)
            # sparse mask
            sparse_mask = (sparsified_data == 0).float()
            if zpb == 0:
                if sparse_mask.mean() != 0:
                    raise AssertionError(
                        f"Expected sparse_mask.mean() == 0, got {sparse_mask.mean()}"
                    )
            else:
                # Ratio of individual zeros in the tensor
                true_sl = min(max(sl, 0.0), 1.0)
                true_sl = true_sl * zpb / sbs[0] / sbs[1]
                if sparse_mask.mean() != true_sl:
                    raise AssertionError(
                        f"Expected sparse_mask.mean() == {true_sl}, got {sparse_mask.mean()}"
                    )