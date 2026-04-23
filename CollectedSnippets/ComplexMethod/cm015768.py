def test_step(self):
        model = SimpleLinear()
        sparsifier = NearlyDiagonalSparsifier(nearliness=1)
        sparsifier.prepare(model, config=[{"tensor_fqn": "linear1.weight"}])

        for g in sparsifier.groups:
            # Before step
            module = g["module"]
            if (1.0 - module.parametrizations["weight"][0].mask.mean()) != 0:
                raise AssertionError("Expected sparsity level to be 0 before step")

        sparsifier.enable_mask_update = True
        sparsifier.step()
        mask = module.parametrizations["weight"][0].mask
        height, width = mask.shape
        if not torch.all(mask == torch.eye(height, width)):
            raise AssertionError("Expected mask to be identity matrix")

        for g in sparsifier.groups:
            # After step
            module = g["module"]
            if (1.0 - module.parametrizations["weight"][0].mask.mean()) <= 0:
                raise AssertionError(
                    "Expected sparsity level to have increased after step"
                )

        # Test if the mask collapses to all zeros if the weights are randomized
        iters_before_collapse = 1000
        for _ in range(iters_before_collapse):
            model.linear1.weight.data = torch.randn(model.linear1.weight.shape)
            sparsifier.step()
        for g in sparsifier.groups:
            # After step
            module = g["module"]
            if (1.0 - module.parametrizations["weight"][0].mask.mean()) <= 0:
                raise AssertionError("Expected sparsity level to not collapse")