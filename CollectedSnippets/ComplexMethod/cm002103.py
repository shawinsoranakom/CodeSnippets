def test_generate_can_restart_from_cache_and_new_tokens_only(self):
        """
        Test that we can continue generating from past key values, returned from a previous `generate` call, without
        the tokens that correspond to the cached part IF the `attention_mask` is the mask for the FULL sequence
        (including previous tokens)
        """
        model = AutoModelForCausalLM.from_pretrained(
            "hf-internal-testing/tiny-random-MistralForCausalLM", device_map="auto"
        )
        tokenizer = AutoTokenizer.from_pretrained("hf-internal-testing/tiny-random-MistralForCausalLM")

        initial_inputs = tokenizer("Hello, world!", return_tensors="pt").to(model.device)
        generate_kwargs = {
            "use_cache": True,
            "do_sample": False,
            "return_dict_in_generate": True,
            "output_scores": True,
        }

        truncated_outputs = model.generate(**initial_inputs, **generate_kwargs, max_new_tokens=2, min_new_tokens=2)
        full_outputs = model.generate(**initial_inputs, **generate_kwargs, max_new_tokens=4, min_new_tokens=4)

        device = initial_inputs["attention_mask"].device
        new_full_mask = torch.cat((initial_inputs["attention_mask"], torch.ones(1, 2, device=device)), dim=-1)

        # Check that we can restart from FULL sequence and get the same result
        full_sequence_inputs = copy.deepcopy(initial_inputs)
        full_sequence_inputs["input_ids"] = truncated_outputs.sequences
        full_sequence_inputs["attention_mask"] = new_full_mask
        full_sequence_inputs["past_key_values"] = copy.deepcopy(truncated_outputs.past_key_values)
        full_sequence_outputs = model.generate(
            **full_sequence_inputs, **generate_kwargs, max_new_tokens=2, min_new_tokens=2
        )

        # The two sets of generated text and past kv should be equal to each other
        if is_moe_model(model.config):
            atol = rtol = 1e-3
        else:
            atol = rtol = 1e-5
        assert_similar_generate_outputs(full_outputs, full_sequence_outputs, atol=atol, rtol=rtol)
        cache1, cache2 = full_outputs.past_key_values, full_sequence_outputs.past_key_values
        for idx in range(len(cache1)):
            if isinstance(cache1, EncoderDecoderCache):
                for subcache in ["self_attention_cache", "cross_attention_cache"]:
                    torch.testing.assert_close(
                        getattr(cache1, subcache).layers[idx].keys, getattr(cache2, subcache).layers[idx].keys
                    )
                    torch.testing.assert_close(
                        getattr(cache1, subcache).layers[idx].values, getattr(cache2, subcache).layers[idx].values
                    )
            else:
                torch.testing.assert_close(cache1.layers[idx].keys, cache2.layers[idx].keys)
                torch.testing.assert_close(cache1.layers[idx].values, cache2.layers[idx].values)

        # Now, check that we can do the same while only restarting from last tokens IF we pass the full mask
        single_token_inputs = copy.deepcopy(initial_inputs)
        single_token_inputs["input_ids"] = truncated_outputs.sequences[:, -1:]
        single_token_inputs["attention_mask"] = new_full_mask
        single_token_inputs["past_key_values"] = copy.deepcopy(truncated_outputs.past_key_values)
        single_token_outputs = model.generate(
            **single_token_inputs, **generate_kwargs, max_new_tokens=2, min_new_tokens=2
        )

        # Of course we get only the new tokens as outputs here, so slice before performing the check
        full_outputs["sequences"] = full_outputs["sequences"][:, -3:]
        assert_similar_generate_outputs(full_outputs, single_token_outputs, atol=atol, rtol=rtol)
        cache1, cache2 = full_outputs.past_key_values, single_token_outputs.past_key_values
        for idx in range(len(cache1)):
            if isinstance(cache1, EncoderDecoderCache):
                for subcache in ["self_attention_cache", "cross_attention_cache"]:
                    torch.testing.assert_close(
                        getattr(cache1, subcache).layers[idx].keys, getattr(cache2, subcache).layers[idx].keys
                    )
                    torch.testing.assert_close(
                        getattr(cache1, subcache).layers[idx].values, getattr(cache2, subcache).layers[idx].values
                    )
            else:
                torch.testing.assert_close(cache1.layers[idx].keys, cache2.layers[idx].keys)
                torch.testing.assert_close(cache1.layers[idx].values, cache2.layers[idx].values)