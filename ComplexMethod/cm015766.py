def test_step(self):
        model = SimpleLinear()
        sparsifier = WeightNormSparsifier(sparsity_level=0.5)
        sparsifier.prepare(model, config=[{"tensor_fqn": "linear1.weight"}])
        for g in sparsifier.groups:
            # Before step
            module = g["module"]
            if (1.0 - module.parametrizations["weight"][0].mask.mean()) != 0:
                raise AssertionError("Expected sparsity level to be 0 before step")
        sparsifier.enable_mask_update = True
        sparsifier.step()
        self.assertAlmostEqual(
            model.linear1.parametrizations["weight"][0].mask.mean().item(),
            0.5,
            places=2,
        )
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