def test_assisted_decoding_sample(self):
        # In this test we don't check assisted vs non-assisted output -- seeded assisted decoding with sample will not
        # match sample for the same seed, as the forward pass does not return the exact same logits (due to matmul with
        # different shapes, see https://github.com/huggingface/transformers/issues/25420#issuecomment-1775317535).
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
                    "blip2",  # overridden `generate()` for all BLIP models
                    "instructblip",
                    "instructblipvideo",
                ]
            ):
                self.skipTest(reason="May fix in the future: need model-specific fixes")

            # enable cache
            config, inputs_dict = self.prepare_config_and_inputs_for_generate(batch_size=1)

            # force eager attention to support output attentions
            if self.has_attentions:
                config._attn_implementation = "eager"

            # NOTE: assisted generation only works with cache on at the moment.
            if not hasattr(config.get_text_config(), "use_cache"):
                self.skipTest(reason=f"{model_class.__name__} doesn't support caching")

            config.is_decoder = True
            model = model_class._from_config(config, attn_implementation="eager").to(torch_device).eval()
            config = model.config
            # Sets assisted generation arguments such that:
            # a) no EOS is generated, to ensure generation doesn't break early
            # b) the assistant model always generates two tokens when it is called, to ensure the input preparation of
            #    the assistant model is correct
            # c) there are at least two forward passes in the main model, to ensure the input preparation of
            #    the main model is correct
            # d) use a cache type compatible with rollbacks (only dynamic cache atm). Otherwise, there may be
            #     differences vs model-specific default cache
            assistant_model = model
            assistant_model.generation_config.num_assistant_tokens = 2  # see b)
            assistant_model.generation_config.num_assistant_tokens_schedule = "constant"  # see b)
            generation_kwargs = {
                "eos_token_id": -1,  # see a)
                "max_new_tokens": 4,  # see c)
                "num_beams": 1,
                "do_sample": True,
                "assistant_model": assistant_model,
                "output_scores": True,
                "output_logits": True,
                "output_hidden_states": True,
                "output_attentions": self.has_attentions,
                "return_dict_in_generate": True,
                "use_cache": True,
                "cache_implementation": "dynamic_full",  # see d)
            }
            logits_processor_kwargs = self._get_logits_processor_kwargs(config=model.config)
            output_assisted = model.generate(**generation_kwargs, **inputs_dict, **logits_processor_kwargs)

            self._check_generate_outputs(output_assisted, config, use_cache=True)