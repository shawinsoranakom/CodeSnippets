def test_assisted_decoding_matches_greedy_search(self, assistant_type):
        # This test ensures that the assisted generation does not introduce output changes over greedy search.
        # See https://github.com/huggingface/transformers/issues/25420#issuecomment-1775317535 for more info.
        # NOTE: It breaks the pattern in the tests above, for multiple reasons:
        # - assisted_decoding, contrarily to the other methods, can't be called on its own (e.g. needs to
        # prepare the assistant encoder outputs in the main generate body);
        # - assisted_decoding does not support `use_cache = False`
        # - assisted_decoding does not support `batch_size > 1`

        for model_class in self.all_generative_model_classes:
            if model_class._is_stateful:
                self.skipTest(reason="Stateful models don't support assisted generation")
            if any(model_name in model_class.__name__.lower() for model_name in ["reformer"]):
                self.skipTest(reason="Won't fix: old model with different cache format")
            if any(
                model_name in model_class.__name__.lower()
                for model_name in [
                    "moshi",
                    "git",
                    "prophetnet",
                    "mllama",  # special cache sizes
                    "blip2",  # overridden `generate()` all BLIP models
                    "instructblip",
                    "instructblipvideo",
                ]
            ):
                self.skipTest(reason="May fix in the future: need model-specific fixes")

            # Set seed for deterministic test - ensures reproducible model initialization and inputs
            set_seed(42)
            # enable cache
            config, inputs_dict = self.prepare_config_and_inputs_for_generate(batch_size=1)
            set_config_for_less_flaky_test(config)

            # force eager attention to support output attentions
            if self.has_attentions:
                config._attn_implementation = "eager"

            # NOTE: assisted generation only works with cache on at the moment.
            if not hasattr(config.get_text_config(), "use_cache"):
                self.skipTest(reason=f"{model_class.__name__} doesn't support caching")

            config.is_decoder = True
            model = model_class._from_config(config, attn_implementation="eager").to(torch_device).eval()
            set_model_for_less_flaky_test(model)
            config = model.config
            # Sets assisted generation arguments such that:
            # a) no EOS is generated, to ensure generation doesn't break early
            # b) the assistant model always generates two tokens when it is called, to ensure the input preparation of
            #    the assistant model is correct
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

            # test with the same assistant model or randomly init one
            # in the first case all candidate tokens are accepted, in the second none is accepted
            # case when some are accepted and some not is hard to reproduce, so let's hope this catches most errors :)
            if assistant_type == "random":
                assistant_model = model_class(config).to(torch_device).eval()
            else:
                assistant_model = model
            assistant_model.config._attn_implementation = "eager"
            assistant_model.generation_config.num_assistant_tokens = 2  # see b)
            assistant_model.generation_config.num_assistant_tokens_schedule = "constant"  # see b)
            generation_kwargs.update({"assistant_model": assistant_model})
            output_assisted = model.generate(**generation_kwargs, **inputs_dict, **logits_processor_kwargs)

            # `gpt_oss` seems to have larger differences on CPU every other generated tokens, sth. like
            # 1e-9, 1e-5, 1e-9, 1e-5. While on GPU, they are all very small 1e-9.
            if is_moe_model(config):
                atol = rtol = 1e-3
            else:
                atol = rtol = 1e-5

            # The two outputs must match and their shape must be as expected
            assert_similar_generate_outputs(output_greedy, output_assisted, atol=atol, rtol=rtol)
            for output in (output_greedy, output_assisted):
                self._check_generate_outputs(output, model.config, use_cache=True)