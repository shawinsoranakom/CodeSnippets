def test_generate_from_inputs_embeds(self, _, num_beams):
        """Tests that we can generate from `inputs_embeds` instead of `input_ids` in LLMs, VLMs, etc"""
        # When supported, tests that the decoder model can generate from `inputs_embeds` instead of `input_ids`
        # if fails, you should probably update the `prepare_inputs_for_generation` function
        for model_class in self.all_generative_model_classes:
            # Set seed for deterministic test - ensures reproducible model initialization and inputs
            set_seed(42)
            config, inputs_dict = self.prepare_config_and_inputs_for_generate()

            # This test is for decoder-only models (encoder-decoder models have native input embeddings support in the
            # decoder)
            if config.is_encoder_decoder:
                continue
            config.is_decoder = True

            set_config_for_less_flaky_test(config)
            # Skip models without explicit support
            model = model_class(config).to(torch_device).eval()
            set_model_for_less_flaky_test(model)
            if "inputs_embeds" not in inspect.signature(model.prepare_inputs_for_generation).parameters:
                continue

            # There are a few exception patterns in this test:
            # 1 - Complex `inputs_embeds` computation, i.e. the correct computation of inputs embeds is more complex
            # than calling the embedding layer with `input_ids`. Subcases of this exception:
            #   1.A - Ignore `scale_embedding`, if the model supports it (it is controlled by a model-dependent flag)
            if hasattr(config, "scale_embedding"):
                config.scale_embedding = False
            # HACK - in the case of granite speech, input_features and inputs_embeds are mutually exclusive;
            # this is similar to VLMs and should likely be standardized for similar audio models in the future,
            # then made generic here.
            if "granitespeech" in model_class.__name__.lower():
                inputs_dict.pop("input_features", None)

            #   1.B - No easy fix, let's skip the check that compares the outputs from `input_ids` and `inputs_embeds`
            has_complex_embeds_computation = any(
                model_name in model_class.__name__.lower() for model_name in ["moshi"]
            )
            # 2 - `inputs_dict` doesn't contain `attention_mask`. When `attention_mask` is not passed to generate,
            # we infer it from `input_ids`. The last test case will fail if there is a pad token in the original input.
            missing_attention_mask = "attention_mask" not in inputs_dict

            # Traditional way of generating text
            input_ids = inputs_dict.pop("input_ids")
            generation_kwargs = {
                "return_dict_in_generate": True,
                "output_scores": True,
                "num_beams": num_beams,
                "do_sample": False,
                "max_new_tokens": 5,
                "min_new_tokens": 5,  # generate exactly 5 tokens
                "use_cache": True,
            }
            outputs_from_ids = model.generate(input_ids=input_ids, **generation_kwargs, **inputs_dict)
            self.assertEqual(outputs_from_ids.sequences.shape[:2], (input_ids.shape[0], input_ids.shape[1] + 5))

            # Same thing, but from input embeddings (`input_ids` is passed so the prompt is present in the output).
            # The output of the two calls should be the same.
            inputs_embeds = model.get_input_embeddings()(input_ids)
            outputs_from_embeds = model.generate(
                input_ids=input_ids, inputs_embeds=inputs_embeds, **generation_kwargs, **inputs_dict
            )
            if is_moe_model(config):
                atol = rtol = 1e-3
            else:
                atol = rtol = 1e-5
            if not has_complex_embeds_computation:
                assert_similar_generate_outputs(outputs_from_ids, outputs_from_embeds, atol=atol, rtol=rtol)

            # input_ids is not a required input on most models -- if we don't pass it, the newly generated tokens will
            # be the same
            if not missing_attention_mask:
                outputs_from_embeds_wo_ids = model.generate(
                    inputs_embeds=inputs_embeds, **generation_kwargs, **inputs_dict
                )
                outputs_from_embeds.sequences = outputs_from_embeds.sequences[:, inputs_embeds.shape[1] :]
                assert_similar_generate_outputs(outputs_from_embeds_wo_ids, outputs_from_embeds, atol=atol, rtol=rtol)