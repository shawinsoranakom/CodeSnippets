def test_generate_compile_model_forward_fullgraph(self):
        """
        Tests that `.generate` is compatible with torch.compile, keeping the same results. Also confirms that
        `.forward` called from `.generate` sees no graph breaks or recompilations when compiled.

        ⚠️ Runs two sequential generations to ensure the cache doesn't get stuck after the first compiled run! ⚠️
        """
        for model_class in self.all_generative_model_classes:
            # 1. Test exclusion criteria
            if not model_class._can_compile_fullgraph:
                self.skipTest("This model doesn't support compilation without graph breaks")

            # 2. Prepares two sets of inputs
            config, inputs_dict = self.prepare_config_and_inputs_for_generate(batch_size=4)
            set_config_for_less_flaky_test(config)
            model = model_class(config).to(torch_device)
            set_model_for_less_flaky_test(model)
            model.eval()  # otherwise `self.training` is `True` -- this flag is used at attn mask creation time

            # Some composite models have a custom generate and will call an inner model's generate -> that inner model
            # is the one that gets compiled.
            # (Note for the future: if BLIP starts causing problems, let's stop testing it)
            if "blip" in model.__class__.__name__.lower():
                model_to_be_compiled = model.language_model
            else:
                model_to_be_compiled = model

            # creates two sets of *different* inputs with the same shape
            main_input = inputs_dict[model.main_input_name].to(torch_device)
            half_batch_size = main_input.shape[0] // 2
            input_1 = {}
            input_2 = {}
            for key, value in inputs_dict.items():
                if isinstance(value, torch.Tensor):
                    input_1[key] = value[:half_batch_size, :].to(torch_device)
                    input_2[key] = value[half_batch_size : half_batch_size * 2, :].to(torch_device)
                else:
                    input_1[key] = value
                    input_2[key] = value
            model_input_sets = [input_1, input_2]
            self.assertTrue(
                model_input_sets[0][model.main_input_name].shape == model_input_sets[1][model.main_input_name].shape
            )

            # 3. compilation-specific setup and generation parameterization
            torch.compiler.reset()  # prevent cached compilation from being used in the test
            has_defined_cache_implementation = model.generation_config.cache_implementation is not None
            compile_config = CompileConfig(fullgraph=True, dynamic=False)  # Error out on dynamic shapes
            compile_config._compile_all_devices = True  # force compilation (e.g. fast CI, CPU)

            generation_kwargs = {
                "use_cache": True,
                "do_sample": False,
                "max_new_tokens": 5,
                "return_dict_in_generate": True,
                "output_scores": True,
                "compile_config": compile_config,
            }

            # 4. get eager + dynamic cache results for future comparison
            dynamic_outputs = []
            # Ignores all `torch.compile` usage, useful to test models that that have non-default compilable caches
            # (who would have used compilation in this section)
            with torch.compiler.set_stance("force_eager"):
                for model_inputs in model_input_sets:
                    gen_out = model.generate(**model_inputs, **generation_kwargs)
                    dynamic_outputs.append(gen_out)
                    # sanity checks for the default cache implementation
                    if not has_defined_cache_implementation:
                        decoder_cache = (
                            gen_out.past_key_values.self_attention_cache
                            if config.is_encoder_decoder
                            else gen_out.past_key_values
                        )
                        self.assertTrue(isinstance(decoder_cache, DynamicCache))
                        self.assertFalse(decoder_cache.is_compileable)
                        # our auto compile should NOT have been called
                        self.assertFalse(hasattr(model_to_be_compiled, "_compiled_call"))

            # 5. get compiled results -- relies on the automatic compilation triggered by specific compilable caches
            if not has_defined_cache_implementation:
                generation_kwargs["cache_implementation"] = "static"

            compiled_outputs = []
            # Uses a context manager to catch recompilation logs. If there is any recompilation, this test fails.
            # Try/Finally is used to ensure that the log options are reset even if an error is raised.
            try:
                torch._logging.set_logs(recompiles_verbose=True)
                logger = logging.get_logger("torch._dynamo.guards")
                with CaptureLogger(logger) as cl:
                    for model_inputs in model_input_sets:
                        # with torch.compiler.set_stance("fail_on_recompile"):
                        gen_out = model.generate(**model_inputs, **generation_kwargs)
                        compiled_outputs.append(gen_out)
                        # sanity checks
                        decoder_cache = (
                            gen_out.past_key_values.self_attention_cache
                            if config.is_encoder_decoder
                            else gen_out.past_key_values
                        )
                        self.assertFalse(isinstance(decoder_cache, DynamicCache))
                        self.assertTrue(decoder_cache.is_compileable)
                        # our auto compile should have been called
                        self.assertTrue(hasattr(model_to_be_compiled, "_compiled_call"))
            finally:
                torch._logging.set_logs()

            # Compilation of sliding layers necessarily has recompiles with `dynamic=False` - however this test
            # still checks that `fullgraph=True` is supported in this case, as compilation with `dynamic=None`
            # is the default and does not actually lead to too many recompiles
            has_sliding_layers = any(decoder_cache.is_sliding)
            has_recompilation = "Recompiling" in cl.out or ("guard" in cl.out and "failure" in cl.out)
            if not has_sliding_layers and has_recompilation:
                raise RuntimeError(
                    f"`torch.compile` recompiled part of the forward pass in {model.__class__.__name__}. "
                    "See the test logs for more details."
                )

            if is_moe_model(config):
                atol = rtol = 1e-3
            else:
                atol = rtol = 1e-5
            for dynamic_result, compiled_result in zip(dynamic_outputs, compiled_outputs):
                assert_similar_generate_outputs(dynamic_result, compiled_result, atol=atol, rtol=rtol)