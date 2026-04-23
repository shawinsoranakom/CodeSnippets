def test_generate_compilation_all_outputs(self):
        """
        Tests that all optional outputs are behaving as expected when compilation is triggered.
        In essence, it's the same as `test_greedy_generate_dict_outputs`, but with automatic compilation triggered.
        """
        for model_class in self.all_generative_model_classes:
            # Here, we should ideally not skip any model, and test them all. However, some old models cannot correctly
            # use a static cache because they don't create the causal masks correctly.
            # TODO: cyril -> relax this by adding a `_support_static_cache` attribute
            if not model_class._can_compile_fullgraph:
                self.skipTest(reason="This model does not support the static cache format")

            config, inputs_dict = self.prepare_config_and_inputs_for_generate()
            if self.has_attentions:
                config._attn_implementation = "eager"  # can't output attentions otherwise
            model = model_class(config).to(torch_device).eval()

            # compilation-specific setup
            torch.compiler.reset()  # prevent cached compilation from being used in the test
            has_defined_cache_implementation = model.generation_config.cache_implementation is not None

            # BLIP is the only exception with custom generate which call `self.lm.generate()`
            # We should avoid such calls in all subsequent multimodal models and try to make `generate()`
            # compatible with multimodality
            compile_config = CompileConfig()
            compile_config._compile_all_devices = True
            if "blip" in model.__class__.__name__.lower():
                model.language_model.generation_config.compile_config = compile_config
                if not has_defined_cache_implementation:
                    model.language_model.generation_config.cache_implementation = "static"
            else:
                # force compilation (e.g. fast CI, CPU)
                model.generation_config.compile_config = compile_config
                if not has_defined_cache_implementation:
                    model.generation_config.cache_implementation = "static"

            logits_processor_kwargs = self._get_logits_processor_kwargs(do_sample=False, config=model.config)
            output_generate = model.generate(
                do_sample=False,
                num_beams=1,
                max_new_tokens=self.max_new_tokens,
                min_new_tokens=self.max_new_tokens,
                output_attentions=True,
                output_hidden_states=True,
                output_scores=True,
                output_logits=True,
                return_dict_in_generate=True,
                use_cache=True,
                **logits_processor_kwargs,
                **inputs_dict,
            )

            if "blip" in model.__class__.__name__.lower():
                self.assertTrue(hasattr(model.language_model, "_compiled_call"))
            else:
                self.assertTrue(hasattr(model, "_compiled_call"))  # our auto compile should have been called

            if model.config.is_encoder_decoder:
                self.assertTrue(output_generate.sequences.shape[1] == self.max_new_tokens + 1)
                self.assertIsInstance(output_generate, GenerateEncoderDecoderOutput)
            else:
                self.assertTrue(
                    output_generate.sequences.shape[1] == self.max_new_tokens + inputs_dict["input_ids"].shape[1]
                )
                self.assertIsInstance(output_generate, GenerateDecoderOnlyOutput)

            self._check_generate_outputs(output_generate, model.config, use_cache=True)