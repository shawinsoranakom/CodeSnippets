def _check_attentions_for_generate(
        self, batch_size, attentions, prompt_length, output_length, config, decoder_past_key_values
    ):
        # Mllama has cross attention layers and those have a different shape than normal attention layers
        self.assertIsInstance(attentions, tuple)
        self.assertListEqual(
            [isinstance(iter_attentions, tuple) for iter_attentions in attentions], [True] * len(attentions)
        )
        self.assertEqual(len(attentions), (output_length - prompt_length))

        cross_attention_layers = self.model_tester.text_config["cross_attention_layers"]
        use_cache = decoder_past_key_values is not None

        for generated_length, iter_attentions in enumerate(attentions):
            # regardless of using cache, the first forward pass will have the full prompt as input
            if use_cache and generated_length > 0:
                model_input_length = 1
            else:
                model_input_length = prompt_length + generated_length
            query_length = prompt_length + generated_length

            expected_shape = (
                batch_size,
                config.num_attention_heads,
                model_input_length,
                query_length,
            )

            expected_shape_cross = (
                batch_size,
                config.num_attention_heads,
                model_input_length,
                self.model_tester.image_length,
            )

            expected_shapes = [
                expected_shape if layer_idx not in cross_attention_layers else expected_shape_cross
                for layer_idx in range(len(iter_attentions))
            ]

            self.assertListEqual([layer_attention.shape for layer_attention in iter_attentions], expected_shapes)