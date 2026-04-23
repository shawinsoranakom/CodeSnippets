def _test_linear_on_device(
        self, model, config, expected_shape, device, also_prune_bias
    ):
        model = model.to(device)
        model.eval()
        num_original_params = sum(p.numel() for p in model.parameters())
        x = torch.ones(128, 7, device=device)

        pruner = ImplementedPruner({"prune_bias": also_prune_bias})
        pruner.prepare(model, config)
        pruner.enable_mask_update = True
        pruner.step()

        y_expected = model(x)

        if y_expected.shape != (128, 10):
            raise AssertionError(f"Expected shape (128, 10), got {y_expected.shape}")
        self._check_pruner_prepared(model, pruner, device)

        # Pruning step
        pruned = pruner.prune()
        y_pruned = pruned(x)
        num_pruned_params = sum(p.numel() for p in pruned.parameters())

        if y_pruned.shape != expected_shape:
            raise AssertionError(
                f"Expected shape {expected_shape}, got {y_pruned.shape}"
            )
        self._check_pruner_pruned(model, pruner, device)
        if y_pruned.shape == y_expected.shape:
            if not torch.isclose(y_expected, y_pruned, rtol=1e-05, atol=1e-07).all():
                raise AssertionError("Expected and pruned outputs are not close")
            if num_pruned_params >= num_original_params:
                raise AssertionError(
                    f"Expected pruned params ({num_pruned_params}) < original ({num_original_params})"
                )