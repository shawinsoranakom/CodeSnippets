def test_lstm_saliency_pruner_update_mask(self):
        model = LSTMLinearModel(
            input_dim=2,
            hidden_dim=2,
            output_dim=2,
            num_layers=1,
        )

        manual_weights = torch.Tensor(
            [[1, 1], [2, 2], [2, 2], [1, 1], [-1, -1], [-2, -2], [-2, -2], [-1, -1]]
        )

        with torch.no_grad():
            model.lstm.weight_ih_l0 = nn.Parameter(manual_weights)
            model.lstm.weight_hh_l0 = nn.Parameter(torch.Tensor(manual_weights))
            model.lstm.bias_ih_l0 = nn.Parameter(manual_weights[:, 0])
            model.lstm.bias_hh_l0 = nn.Parameter(manual_weights[:, 0])

        config = [
            {"tensor_fqn": "lstm.weight_ih_l0"},
            {"tensor_fqn": "lstm.weight_hh_l0"},
        ]
        lstm_input = torch.ones((1, 2))
        fx_pruner = LSTMSaliencyPruner({"sparsity_level": 0.5})
        fx_pruner.prepare(model, config)
        fx_pruner.enable_mask_update = True
        fx_pruner.step()

        model.eval()
        pruned_model = fx_pruner.prune()
        pruned_model.eval()

        # make sure both models run
        model(lstm_input)
        pruned_model(lstm_input)

        # make sure lowest saliency rows are pruned
        expected = torch.Tensor([[2, 2], [2, 2], [-2, -2], [-2, -2]])
        pruned = model.lstm.weight_ih_l0
        if expected.shape != pruned.shape:
            raise AssertionError(f"Expected shape {expected.shape}, got {pruned.shape}")
        if not torch.isclose(expected, pruned, rtol=1e-05, atol=1e-07).all():
            raise AssertionError("Expected and pruned tensors are not close")

        expected = torch.Tensor([[2], [2], [-2], [-2]])
        pruned = model.lstm.weight_hh_l0
        if expected.shape != pruned.shape:
            raise AssertionError(f"Expected shape {expected.shape}, got {pruned.shape}")
        if not torch.isclose(expected, pruned, rtol=1e-05, atol=1e-07).all():
            raise AssertionError("Expected and pruned tensors are not close")

        expected = torch.Tensor([2, 2, -2, -2])
        for pruned in [model.lstm.bias_ih_l0, model.lstm.bias_hh_l0]:
            if expected.shape != pruned.shape:
                raise AssertionError(
                    f"Expected shape {expected.shape}, got {pruned.shape}"
                )
            if not torch.isclose(expected, pruned, rtol=1e-05, atol=1e-07).all():
                raise AssertionError("Expected and pruned tensors are not close")