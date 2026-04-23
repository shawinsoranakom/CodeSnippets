def test_create_network_inputs(self, prediction_length, context_length, lags_sequence):
        history_length = max(lags_sequence) + context_length

        config = TimeSeriesTransformerConfig(
            prediction_length=prediction_length,
            context_length=context_length,
            lags_sequence=lags_sequence,
            scaling=False,
            num_parallel_samples=10,
            num_static_categorical_features=1,
            cardinality=[1],
            embedding_dimension=[2],
            num_static_real_features=1,
        )
        model = TimeSeriesTransformerModel(config)

        batch = {
            "static_categorical_features": torch.tensor([[0]], dtype=torch.int64),
            "static_real_features": torch.tensor([[0.0]], dtype=torch.float32),
            "past_time_features": torch.arange(history_length, dtype=torch.float32).view(1, history_length, 1),
            "past_values": torch.arange(history_length, dtype=torch.float32).view(1, history_length),
            "past_observed_mask": torch.arange(history_length, dtype=torch.float32).view(1, history_length),
        }

        # test with no future_target (only one step prediction)
        batch["future_time_features"] = torch.arange(history_length, history_length + 1, dtype=torch.float32).view(
            1, 1, 1
        )
        transformer_inputs, loc, scale, _ = model.create_network_inputs(**batch)

        self.assertTrue((scale == 1.0).all())
        assert (loc == 0.0).all()

        ref = torch.arange(max(lags_sequence), history_length, dtype=torch.float32)

        for idx, lag in enumerate(lags_sequence):
            assert torch.isclose(ref - lag, transformer_inputs[0, :, idx]).all()

        # test with all future data
        batch["future_time_features"] = torch.arange(
            history_length, history_length + prediction_length, dtype=torch.float32
        ).view(1, prediction_length, 1)
        batch["future_values"] = torch.arange(
            history_length, history_length + prediction_length, dtype=torch.float32
        ).view(1, prediction_length)
        transformer_inputs, loc, scale, _ = model.create_network_inputs(**batch)

        assert (scale == 1.0).all()
        assert (loc == 0.0).all()

        ref = torch.arange(max(lags_sequence), history_length + prediction_length, dtype=torch.float32)

        for idx, lag in enumerate(lags_sequence):
            assert torch.isclose(ref - lag, transformer_inputs[0, :, idx]).all()

        # test for generation
        batch.pop("future_values")
        transformer_inputs, loc, scale, _ = model.create_network_inputs(**batch)

        lagged_sequence = model.get_lagged_subsequences(
            sequence=batch["past_values"],
            subsequences_length=1,
            shift=1,
        )
        # assert that the last element of the lagged sequence is the one after the encoders input
        assert transformer_inputs[0, ..., 0][-1] + 1 == lagged_sequence[0, ..., 0][-1]

        future_values = torch.arange(history_length, history_length + prediction_length, dtype=torch.float32).view(
            1, prediction_length
        )
        # assert that the first element of the future_values is offset by lag after the decoders input
        assert lagged_sequence[0, ..., 0][-1] + lags_sequence[0] == future_values[0, ..., 0]