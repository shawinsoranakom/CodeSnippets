def test_sparsity_levels(self):
        sparsity_levels = [-1.0, 0.0, 0.5, 1.0, 2.0]
        sparse_block_shapes = [(1, 1), (1, 4), (2, 2), (4, 1)]
        zeros_per_blocks = [0, 1, 2, 3, 4]

        testcases = itertools.tee(
            itertools.product(sparsity_levels, sparse_block_shapes, zeros_per_blocks)
        )
        # Create a config and model with all the testcases
        model = nn.Sequential()
        sparsifier = WeightNormSparsifier()

        sparsity_per_layer_config = []
        p = re.compile(r"[-\.\s]")
        for sl, sbs, zpb in testcases[0]:
            # Make sure the number of zeros is not > values in a block
            if zpb > sbs[0] * sbs[1]:
                continue
            layer_name = f"{sl}_{sbs}_{zpb}"
            layer_name = p.sub("_", layer_name)

            layer = nn.Linear(12, 12, bias=False)
            layer.weight = nn.Parameter(torch.ones(12, 12))
            model.add_module(layer_name, layer)
            config = {
                "tensor_fqn": layer_name + ".weight",
                "sparsity_level": sl,
                "sparse_block_shape": sbs,
                "zeros_per_block": zpb,
            }
            sparsity_per_layer_config.append(config)

        sparsifier.prepare(model, sparsity_per_layer_config)
        sparsifier.step()
        sparsifier.squash_mask()
        model.eval()

        for sl, sbs, zpb in testcases[1]:
            if zpb > sbs[0] * sbs[1]:
                continue
            layer_name = f"{sl}_{sbs}_{zpb}"
            layer_name = p.sub("_", layer_name)
            layer = getattr(model, layer_name)

            # Level of sparsity is achieved
            sparse_mask = (layer.weight == 0).float()
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