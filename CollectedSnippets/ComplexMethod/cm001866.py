def test_generation_beyond_sliding_window_dynamic(self, attn_implementation: str):
        """
        Same as above, but explicitly setting the cache to Dynamic, as it's otherwise static by default for
        the model on the hub
        """
        # Impossible to test it with this model (even with < 100 tokens), probably due to the compilation of a large model.
        if attn_implementation == "flex_attention":
            self.skipTest(
                reason="`flex_attention` gives `torch._inductor.exc.InductorError: RuntimeError: No valid triton configs. OutOfMemoryError: out of resource: triton_tem_fused_0 Required: 147456 Hardware limit:101376 Reducing block sizes or `num_stages` may help.`"
            )

        if (
            attn_implementation == "flash_attention_2"
            and not is_flash_attn_2_available()
            and not (is_torch_xpu_available() and is_kernels_available())
        ):
            self.skipTest("FlashAttention2 is required for this test.")

        model_id = "google/vaultgemma-1b"
        EXPECTED_COMPLETIONS = [
            " place pretty place pretty place. place pretty place pretty place. place pretty place pretty place. place pretty",
            ", green, yellow, orange, purple, black, white, and gray.\n\nA list of",
        ]

        input_text = [
            "This is a nice place. " * 800 + "I really enjoy the scenery,",  # This is larger than 4096 tokens
            "A list of colors: red, blue",  # This will almost all be padding tokens
        ]
        tokenizer = AutoTokenizer.from_pretrained(model_id, padding="left")
        inputs = tokenizer(input_text, padding=True, return_tensors="pt").to(torch_device)

        model = AutoModelForCausalLM.from_pretrained(
            model_id, attn_implementation=attn_implementation, dtype=torch.float16
        ).to(torch_device)

        # Make sure prefill is larger than sliding window
        input_size = inputs.input_ids.shape[-1]
        self.assertTrue(input_size > model.config.sliding_window)

        out = model.generate(**inputs, max_new_tokens=20, cache_implementation="dynamic", return_dict_in_generate=True)
        output_text = tokenizer.batch_decode(out.sequences[:, input_size:])

        self.assertEqual(output_text, EXPECTED_COMPLETIONS)

        # Let's check that the dynamic cache has hybrid layers!
        dynamic_cache = out.past_key_values
        self.assertTrue(isinstance(dynamic_cache, DynamicCache))
        for layer, layer_type in zip(dynamic_cache.layers, model.config.layer_types):
            if layer_type == "sliding_attention":
                self.assertTrue(isinstance(layer, DynamicSlidingWindowLayer))
                self.assertEqual(layer.keys.shape[-2], model.config.sliding_window - 1)
            else:
                self.assertTrue(isinstance(layer, DynamicLayer))
                # max_new_tokens - 1 because last token generated is not cached
                self.assertEqual(layer.keys.shape[-2], input_size + 20 - 1)