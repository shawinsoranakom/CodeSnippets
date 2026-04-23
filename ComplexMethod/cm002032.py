def test_generate_continue_from_past_key_values(self):
        # Tests that we can continue generating from past key values, returned from a previous `generate` call
        for model_class in self.all_generative_model_classes:
            if model_class == self.model_tester.token_classification_class:
                continue
            if any(model_name in model_class.__name__.lower() for model_name in ["imagegpt", "mllama"]):
                self.skipTest(reason="Won't fix: old model with unique inputs/caches/other")
            if any(model_name in model_class.__name__.lower() for model_name in ["umt5"]):
                self.skipTest(reason="TODO: needs modeling or test input preparation fixes for compatibility")

            config, inputs = self.model_tester.prepare_config_and_inputs_for_common()

            if not hasattr(config.get_text_config(), "use_cache"):
                self.skipTest(reason=f"{model_class.__name__} doesn't support caching")

            # Let's make it always:
            # 1. use cache (for obvious reasons)
            # 2. generate to max length (which can be achieved by setting the eos token to an invalid value), which
            #    would make the test flaky (e.g. EOS is generated on iteration 1 on both generations, but the
            #    continuation would force it to generate beyond an EOS token)
            # 3. ignore `token_type_ids` for simplicity
            # 4. ignore `forced_eos_token_id`, which requires further manipulation of the continuation inputs and is
            #    active by default on some models
            # 5. ignore `encoder_no_repeat_ngram_size`, which is set by default in some encoder-decoder models. When
            #    we use their decoder as a stand-alone model, `encoder_no_repeat_ngram_size` actually prevents
            #    repetition exclusively from the prompt. This test relies on comparing one call vs 2 calls
            #    with cache, what is considered a prompt is different in the two cases.

            if "token_type_ids" in inputs:
                del inputs["token_type_ids"]

            model = model_class(config).to(torch_device)
            model.eval()

            # If "past_key_values" is not returned, skip the test (e.g. RWKV uses a different cache name and format)
            outputs = model(**inputs)
            if "past_key_values" not in outputs:
                self.skipTest(reason="This model doesn't return `past_key_values`")

            generate_kwargs = {
                "pad_token_id": -1,
                "eos_token_id": -1,
                "forced_eos_token_id": None,
                "encoder_no_repeat_ngram_size": 0,
                "use_cache": True,
                "do_sample": False,
                "return_dict_in_generate": True,
                "output_scores": True,
            }

            # Traditional way of generating text, with `return_dict_in_generate` to return the past key values
            outputs = model.generate(**inputs, **generate_kwargs, max_new_tokens=4)

            # Let's generate again, but passing the past key values in between (3 + 1 = 4 tokens). Note that the
            # inputs may need to be tweaked across `generate` calls (like the attention mask).
            outputs_cached = model.generate(**inputs, **generate_kwargs, max_new_tokens=3)

            # Continue from the tokens generated above, preparing the inputs accordingly
            inputs["past_key_values"] = outputs_cached.past_key_values
            new_attention_len = outputs_cached.sequences.shape[-1]

            # It must be encoder-decoder models
            self.assertTrue(config.is_encoder_decoder)

            inputs["decoder_input_ids"] = outputs_cached.sequences
            if "decoder_attention_mask" in inputs:
                decoder_attention_mask = inputs["decoder_attention_mask"]

                # Add BOS mask: the new sequence comes with a new BOS token, which is not included in the original inputs
                padding_tensor = torch.ones_like(decoder_attention_mask[:, :1])
                decoder_attention_mask = torch.cat([padding_tensor, decoder_attention_mask], dim=1)

                inputs["decoder_attention_mask"] = torch.nn.functional.pad(
                    decoder_attention_mask,
                    (0, new_attention_len - decoder_attention_mask.shape[1]),
                    mode="constant",
                    value=1,
                )

            first_caches_scores = outputs_cached.scores
            outputs_cached = model.generate(**inputs, **generate_kwargs, max_new_tokens=1)
            full_cached_scores = first_caches_scores + outputs_cached.scores
            outputs_cached.scores = full_cached_scores

            # The two sets of generated text and past kv should be equal to each other
            assert_similar_generate_outputs(outputs, outputs_cached)
            self._check_caches_are_equal(outputs.past_key_values, outputs_cached.past_key_values)