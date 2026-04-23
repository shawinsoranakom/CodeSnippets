def _test_update_mask_on_multiple_layer(
        self, expected_conv1, expected_conv2, device
    ):
        # the second setting
        model = TestFPGMPruner.SimpleConvFPGM().to(device)
        x = torch.ones((1, 1, 32, 32), device=device)
        pruner = FPGMPruner(0.3)
        config = [
            {"tensor_fqn": "conv2d1.weight"},
            {"tensor_fqn": "conv2d2.weight", "sparsity_level": 0.5},
        ]
        pruner.prepare(model, config)
        pruner.enable_mask_update = True
        pruner.step()
        # Get the masks for the two least-norm filters
        mask1 = pruner.groups[0]["module"].parametrizations.weight[0].mask[-1]
        mask2 = pruner.groups[0]["module"].parametrizations.weight[0].mask[-2]
        # Check if either of the least-norm filters is not pruned
        if not (mask1.item() is not False or mask2.item() is not False):
            raise AssertionError("Do not prune all least-norm filters")

        # fusion step
        pruned_model = pruner.prune()
        pruned_y = pruned_model(x)
        # assert shapes
        expected_conv1 = expected_conv1.to(device)
        expected_conv2 = expected_conv2.to(device)
        if pruned_y.shape != (1, 2, 32, 32):
            raise AssertionError(f"Expected shape (1, 2, 32, 32), got {pruned_y.shape}")
        if pruned_model.conv2d1.weight.shape != expected_conv1.shape:
            raise AssertionError(
                f"Expected conv2d1 shape {expected_conv1.shape}, got {pruned_model.conv2d1.weight.shape}"
            )
        if pruned_model.conv2d2.weight.shape != expected_conv2.shape:
            raise AssertionError(
                f"Expected conv2d2 shape {expected_conv2.shape}, got {pruned_model.conv2d2.weight.shape}"
            )
        # assert values
        if not torch.isclose(
            pruned_model.conv2d1.weight, expected_conv1, rtol=1e-05, atol=1e-07
        ).all():
            raise AssertionError("conv2d1 weight does not match expected")
        if not torch.isclose(
            pruned_model.conv2d2.weight, expected_conv2, rtol=1e-05, atol=1e-07
        ).all():
            raise AssertionError("conv2d2 weight does not match expected")