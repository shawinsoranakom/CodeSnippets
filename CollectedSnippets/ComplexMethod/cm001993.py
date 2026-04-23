def _check_hidden_states_for_generate(
        self, batch_size, hidden_states, prompt_length, output_length, config, use_cache=False
    ):
        self.assertIsInstance(hidden_states, tuple)
        self.assertListEqual(
            [isinstance(iter_hidden_states, tuple) for iter_hidden_states in hidden_states],
            [True] * len(hidden_states),
        )
        self.assertEqual(len(hidden_states), (output_length - prompt_length))

        # When `output_hidden_states=True`, each iteration of generate appends the hidden states corresponding to the
        # new token(s)
        for generated_length, iter_hidden_states in enumerate(hidden_states):
            # regardless of using cache, the first forward pass will have the full prompt as input
            if use_cache and generated_length > 0:
                model_input_length = 1
            else:
                model_input_length = prompt_length + generated_length

            # check hidden size
            # we can have different hidden sizes between encoder and decoder --> check both
            expected_shape_encoder = (batch_size, model_input_length, config.encoder_config.hidden_size)
            expected_shape_decoder = (batch_size, model_input_length, config.decoder_config.hidden_size)
            self.assertTrue(
                [layer_hidden_states.shape for layer_hidden_states in iter_hidden_states]
                == [expected_shape_encoder] * len(iter_hidden_states)
                or [layer_hidden_states.shape for layer_hidden_states in iter_hidden_states]
                == [expected_shape_decoder] * len(iter_hidden_states)
            )