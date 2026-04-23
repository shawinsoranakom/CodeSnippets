def test_generate_continue_from_inputs_embeds(self):
        """Tests that we can continue generation from `inputs_embeds` and past key values returned from a previous `generate` call."""
        for model_class in self.all_generative_model_classes:
            if any(model_name in model_class.__name__.lower() for model_name in ["imagegpt"]):
                self.skipTest(reason="Won't fix: old model with unique inputs/caches/other")
            if any(model_name in model_class.__name__.lower() for model_name in ["umt5"]):
                self.skipTest(reason="TODO: needs modeling or test input preparation fixes for compatibility")

            config, inputs_dict = self.prepare_config_and_inputs_for_generate()

            if "token_type_ids" in inputs_dict:
                del inputs_dict["token_type_ids"]

            if config.is_encoder_decoder:
                self.skipTest(reason="This model is encoder-decoder")
            # TODO (joao, raushan): the correct line below is `if not hasattr(config.get_text_config(), "use_cache")`,
            # but it breaks a few models. Fix and then apply `has_similar_generate_outputs` pattern
            if not hasattr(config, "use_cache"):
                self.skipTest(reason=f"{model_class.__name__} doesn't support caching")

            model = model_class(config).to(torch_device).eval()

            if "inputs_embeds" not in inspect.signature(model.prepare_inputs_for_generation).parameters:
                self.skipTest(reason="This model does not support `inputs_embeds` in generation")

            # If "past_key_values" is not returned, skip the test (e.g. RWKV uses a different cache name and format)
            outputs = model(**inputs_dict)
            if "past_key_values" not in outputs:
                self.skipTest(reason="This model doesn't return `past_key_values`")

            input_ids = inputs_dict.pop("input_ids")

            model.generation_config.pad_token_id = model.generation_config.eos_token_id = -1
            model.generation_config.forced_eos_token_id = None
            model.config.is_decoder = True
            model.generation_config.use_cache = True

            generation_kwargs = {
                "return_dict_in_generate": True,
                "do_sample": False,
            }

            # Traditional way of generating text, with `return_dict_in_generate` to return the past key values.
            inputs_embeds = model.get_input_embeddings()(input_ids)
            outputs = model.generate(inputs_embeds=inputs_embeds, max_new_tokens=4, **generation_kwargs)

            # Let's generate again, but passing the past key values in between (3 + 1 = 4 tokens)
            initial_output = model.generate(inputs_embeds=inputs_embeds, max_new_tokens=3, **generation_kwargs)
            continued_embeds = torch.cat(
                [inputs_embeds, model.get_input_embeddings()(initial_output.sequences)], dim=1
            )
            cached_output = model.generate(
                inputs_embeds=continued_embeds,
                max_new_tokens=1,
                past_key_values=initial_output.past_key_values,
                **generation_kwargs,
            )

            # Combine the (3 + 1) generated tokens and verify it matches with full generation.
            combined_output_sequences = torch.concat([initial_output.sequences, cached_output.sequences], axis=1)
            self.assertListEqual(outputs.sequences.tolist(), combined_output_sequences.tolist())
            # The two sets of past kv should be equal to each other
            self._check_caches_are_equal(outputs.past_key_values, cached_output.past_key_values)