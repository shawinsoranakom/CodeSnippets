def test_prompt_lookup_decoding_matches_greedy_search(self):
        # This test ensures that the prompt lookup generation does not introduce output changes over greedy search.
        # This test is mostly a copy of test_assisted_decoding_matches_greedy_search

        for model_class in self.all_generative_model_classes:
            if model_class._is_stateful:
                self.skipTest(reason="Stateful models don't support assisted generation")
            old_models = [  # models that we won't commit resources fixing because they are old and have little usage
                # reformer: has a different cache format
                "reformer",
                # imagegpt: the output lm head uses `vocab_size - 1` tokens, so the `NoBadWordsLogitsProcessor` used
                # by prompt lookup may fail
                "imagegpt",
            ]
            if any(model_name in model_class.__name__.lower() for model_name in old_models):
                self.skipTest(reason="Won't fix: old model")
            if any(
                model_name in model_class.__name__.lower()
                for model_name in [
                    "moshi",
                    "git",
                    "prophetnet",
                    "mllama",  # special cache sizes
                    "blip2",  # overridden `generate()` for all BLIP models
                    "instructblip",
                    "instructblipvideo",
                ]
            ):
                self.skipTest(reason="May fix in the future: need model-specific fixes")

            # Set seed for deterministic test - ensures reproducible model initialization and inputs
            set_seed(42)
            # enable cache
            config, inputs_dict = self.prepare_config_and_inputs_for_generate(batch_size=1)

            # force eager attention to support output attentions
            if self.has_attentions:
                config._attn_implementation = "eager"

            # NOTE: assisted generation only works with cache on at the moment.
            if not hasattr(config.get_text_config(), "use_cache"):
                self.skipTest(reason=f"{model_class.__name__} doesn't support caching")

            config.is_decoder = True
            model = model_class(config).to(torch_device).eval()
            # Sets assisted generation arguments such that:
            # a) no EOS is generated, to ensure generation doesn't break early
            # b) the prompt lookup tries to give the model 2 tokens, to ensure the input preparation of
            #    prompt lookup is correct
            # c) there are at least two forward passes in the main model, to ensure the input preparation of
            #    the main model is correct
            # d) use a cache type compatible with rollbacks (only dynamic cache atm). Otherwise, there may be
            #     differences vs model-specific default cache
            generation_kwargs = {
                "eos_token_id": -1,  # see a)
                "max_new_tokens": 4,  # see c)
                "num_beams": 1,
                "do_sample": False,
                "output_scores": True,
                "output_logits": True,
                "output_hidden_states": True,
                "output_attentions": self.has_attentions,
                "return_dict_in_generate": True,
                "use_cache": True,
                "cache_implementation": "dynamic_full",  # see d)
            }
            logits_processor_kwargs = self._get_logits_processor_kwargs(config=model.config)

            output_greedy = model.generate(**generation_kwargs, **inputs_dict, **logits_processor_kwargs)

            generation_kwargs.update({"prompt_lookup_num_tokens": 2})  # see b)
            output_prompt_lookup = model.generate(**generation_kwargs, **inputs_dict, **logits_processor_kwargs)

            # The two outputs must match and their shape must be as expected
            if is_moe_model(config):
                atol = rtol = 1e-3
            else:
                atol = rtol = 1e-5
            assert_similar_generate_outputs(output_greedy, output_prompt_lookup, atol=atol, rtol=rtol)
            for output in (output_greedy, output_prompt_lookup):
                self._check_generate_outputs(output, model.config, use_cache=True)