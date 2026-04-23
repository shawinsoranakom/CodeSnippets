def test_generate_with_static_cache(self):
        """
        Tests that generating with static cache give almost same results as with dynamic cache, and the output cache
        has the expected shapes
        """
        for model_class in self.all_generative_model_classes:
            # Here, we should ideally not skip any model, and test them all. However, some old models cannot correctly
            # use a static cache because they don't create the causal masks correctly.
            # TODO: cyril -> relax this by adding a `_support_static_cache` attribute
            if not model_class._can_compile_fullgraph:
                self.skipTest(reason="This model does not support the static cache format")

            # Set seed for deterministic test - ensures reproducible model initialization and inputs
            set_seed(42)
            config, inputs_dict = self.prepare_config_and_inputs_for_generate()
            set_config_for_less_flaky_test(config)
            main_input = inputs_dict[model_class.main_input_name]

            if config.is_encoder_decoder:
                self.skipTest(reason="This model is encoder-decoder and has Encoder-Decoder Cache")

            config.is_decoder = True
            batch_size = main_input.shape[0]
            seq_length = self.model_tester.seq_length
            max_new_tokens = 20

            for dtype in (torch.float32, torch.float16):
                model = model_class(copy.deepcopy(config)).to(torch_device).to(dtype).eval()
                inputs_dict = {
                    k: v.to(dtype) if isinstance(v, torch.Tensor) and torch.is_floating_point(v) else v
                    for k, v in inputs_dict.items()
                }
                set_model_for_less_flaky_test(model)

                generation_kwargs = {
                    "max_new_tokens": max_new_tokens,
                    "return_dict_in_generate": True,  # Required to return `past_key_values`
                    "output_scores": True,
                    "use_cache": True,
                }

                static_cache_generation = model.generate(
                    **generation_kwargs, **inputs_dict, cache_implementation="static"
                )

                # Check 1: The cache shapes must match the expected shapes
                text_config = model.config.get_text_config()
                max_cache_len = seq_length + max_new_tokens - 1  # cache len = gen len - 1, the last token has no cache
                self.assertTrue(isinstance(static_cache_generation.past_key_values, StaticCache))
                self._check_past_key_values_for_generate(
                    batch_size, static_cache_generation.past_key_values, max_cache_len, text_config
                )

                # Check 2: The outputs must be similar to the case with dynamic cache
                dynamic_cache_generation = model.generate(**generation_kwargs, **inputs_dict)
                if is_moe_model(config):
                    atol = rtol = 1e-3
                else:
                    atol = rtol = 1e-5
                assert_similar_generate_outputs(
                    dynamic_cache_generation, static_cache_generation, atol=atol, rtol=rtol
                )