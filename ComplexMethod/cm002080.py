def _test_continuous_batching_parity(
        self,
        model_id: str,
        continuous_batching_config: ContinuousBatchingConfig,
        attn_implementation: str,
        max_new_tokens: int = 20,
        num_repeat_prompts: int = 1,
    ) -> None:
        """Tests the parity between continuous batching and non-continuous batching generation."""

        # Skip the test if Flash Attention is required but not available
        is_fa = is_flash_attention_requested(requested_attention_implementation=attn_implementation)
        if is_fa and not (is_flash_attn_2_available() or is_kernels_available()):
            self.skipTest("Flash Attention is not available and neither is the kernels library. Skipping test.")
        # Skip the test if cuda graph is on but the device is not CUDA
        if continuous_batching_config.use_cuda_graph and torch_device != "cuda":
            self.skipTest("CUDA graph is only supported on CUDA devices. Skipping test.")

        # If the config turns on compile, change the generation config to use the default mode instead of
        # max-autotune-no-cudagraphs which can change the kernels between generate_batch and generate
        if continuous_batching_config.use_default_compile_configs:
            fullgraph = not is_flash_attention_requested(requested_attention_implementation=attn_implementation)
            compile_config = CompileConfig(mode="default", fullgraph=fullgraph, dynamic=True)
            continuous_batching_config.varlen_compile_config = compile_config

        # Eager and SDPA implementations get a precision boost to account for the fact that an attention mask is used in
        # continuous batching but not in generate
        dtype = "auto" if is_fa else torch.float32

        # Prepare inputs
        tokenizer, model = get_tokenizer_and_model(model_id, attn_implementation, torch_device, dtype)
        if (
            attn_implementation == "flash_attention_2"
            and torch_device == "cpu"
            and getattr(model.config, "sliding_window", None) is not None
            and model.config.sliding_window > 0
        ):
            self.skipTest("Flash Attention 2 with sliding window attention is not supported on CPU. Skipping test.")

        user_messages = _DEFAULT_USER_MESSAGES * num_repeat_prompts
        input_ids = get_generation_inputs(user_messages, tokenizer, for_continuous_batching=True)

        model.generation_config.max_new_tokens = max_new_tokens
        model.generation_config.do_sample = False

        # Generation with continuous batching
        continuous_batching_outputs = model.generate_batch(
            inputs=input_ids,
            generation_config=model.generation_config,
            continuous_batching_config=continuous_batching_config,
        )

        # Prepare non-continuous batching inputs and model
        inputs = get_generation_inputs(user_messages, tokenizer, for_continuous_batching=False)
        num_input_tokens = inputs.input_ids.shape[1]

        # Generation without continuous batching (reload model to avoid any state contamination)
        _, model = get_tokenizer_and_model(model_id, attn_implementation, torch_device, dtype)
        model.generation_config.max_new_tokens = max_new_tokens
        model.generation_config.do_sample = False
        model.generation_config.use_cuda_graph = continuous_batching_config.use_cuda_graph
        model.generation_config.compile_config = continuous_batching_config.varlen_compile_config

        # Create a static cache if compile_config is set, because regular generate requires a compileable cache
        past_key_values = None
        if model.generation_config.compile_config is not None:
            max_cache_len = num_input_tokens + max_new_tokens
            past_key_values = StaticCache(config=model.config, max_cache_len=max_cache_len)

        generate_outputs = model.generate(
            **inputs.to(torch_device), generation_config=model.generation_config, past_key_values=past_key_values
        )

        for i, user_message in enumerate(user_messages):
            # Find the corresponding request in the continuous batching outputs
            input_tokens = inputs.input_ids[i][inputs.attention_mask[i] == 1].tolist()
            key_to_pop = None
            for key, state in continuous_batching_outputs.items():
                if state.prompt_ids == input_tokens:
                    key_to_pop = key
                    break
            if key_to_pop is None:
                self.fail(f"Request {i} not found in continuous batching outputs")
            continuous_batching_output = continuous_batching_outputs.pop(key_to_pop).generated_tokens

            generate_output = generate_outputs[i][num_input_tokens:].tolist()
            while generate_output[-1] == model.generation_config.pad_token_id:
                generate_output.pop()

            if continuous_batching_output != generate_output:
                decoded_continuous_batching_output = tokenizer.decode(continuous_batching_output)
                decoded_generate_output = tokenizer.decode(generate_output)
                msg = f"Test failed for {model_id = } {continuous_batching_config = }, {attn_implementation = }\n"
                msg += f"User message              : {repr(user_message)}\n"
                msg += f"Continuous batching output: {repr(decoded_continuous_batching_output)}\n"
                msg += f"Generate output           : {repr(decoded_generate_output)}"
                self.fail(msg)