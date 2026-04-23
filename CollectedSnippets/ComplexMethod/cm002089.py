def test_generate_from_random_inputs_embeds(self):
        """
        Text-only: Tests that different `inputs_embeds` generate different outputs in models with `main_input=="input_ids"`.
        Some models have 'images' as main input and thus can't generate with random text embeddings.
        See `test_generate_from_inputs_embeds` for more general checks.
        """
        for model_class in self.all_generative_model_classes:
            config, inputs_dict = self.prepare_config_and_inputs_for_generate()

            if config.is_encoder_decoder:
                continue
            config.is_decoder = True

            model = model_class(config).to(torch_device).eval()
            if "inputs_embeds" not in inspect.signature(model.prepare_inputs_for_generation).parameters:
                continue

            #  No easy fix, let's skip the test for now
            has_complex_embeds_computation = any(
                model_name in model_class.__name__.lower() for model_name in ["moshi"]
            )

            if model_class.main_input_name != "input_ids" or has_complex_embeds_computation:
                self.skipTest(
                    "The model's main input name in not `input_ids` and we need kwargs from input dict as well."
                )

            if hasattr(config, "scale_embedding"):
                config.scale_embedding = False

            generation_kwargs = {
                "return_dict_in_generate": True,
                "output_scores": True,
                "do_sample": False,
                "max_new_tokens": 5,
                "min_new_tokens": 5,  # generate exactly 5 tokens
            }

            input_ids = inputs_dict.pop("input_ids")
            inputs_embeds = model.get_input_embeddings()(input_ids)
            outputs_from_embeds = model.generate(input_ids, inputs_embeds=inputs_embeds, **generation_kwargs)

            # If we pass different inputs_embeds, we should get different outputs (the output text may be the
            # same, but the logits will almost surely be different)
            random_embeds = torch.rand_like(inputs_embeds)
            outputs_from_rand_embeds = model.generate(
                input_ids=input_ids, inputs_embeds=random_embeds, **generation_kwargs
            )
            for i in range(len(outputs_from_rand_embeds.scores)):
                self.assertFalse(torch.allclose(outputs_from_embeds.scores[i], outputs_from_rand_embeds.scores[i]))