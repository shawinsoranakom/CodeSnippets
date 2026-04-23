def _test_conv2d_on_device(
        self, model, config, x, expected_shape, device, also_prune_bias
    ):
        model = model.to(device)
        num_original_params = sum(p.numel() for p in model.parameters())
        model.eval()

        pruner = ImplementedPruner({"prune_bias": also_prune_bias})
        pruner.prepare(model, config)
        pruner.enable_mask_update = True
        pruner.step()

        y_expected = model(x)
        if y_expected.shape != expected_shape:
            raise AssertionError(
                f"Expected shape {expected_shape}, got {y_expected.shape}"
            )

        self._check_pruner_prepared(model, pruner, device)

        # Fusion step
        pruned = pruner.prune()
        y_pruned = pruned(x)
        num_pruned_params = sum(p.numel() for p in pruned.parameters())

        if y_pruned.shape != expected_shape:
            raise AssertionError(
                f"Expected shape {expected_shape}, got {y_pruned.shape}"
            )
        self._check_pruner_pruned(model, pruner, device)
        if y_pruned.shape == y_expected.shape:
            # TODO This rtol is a little high, need to double check if something specific is causing this to fail
            if not torch.isclose(y_expected, y_pruned, rtol=1e-3, atol=1e-3).all():
                raise AssertionError(f"fail for {type(model)}")
            # only time this should be equal is when all layers have padding and we can't prune
            if num_pruned_params > num_original_params:
                raise AssertionError(
                    f"Expected pruned params ({num_pruned_params}) <= original ({num_original_params})"
                )