def test_per_request_logits_processors(self, use_cuda_graph: bool, use_async_batching: bool) -> None:
        """Tests that per-request logits processor kwargs (temperature, top_k, top_p) work correctly in generation."""
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        max_new_tokens = 10
        temperatures = [1.0, 1.0]
        top_ks = [10, 50]
        top_ps = [0.9, 0.99]

        tokenizer, model = get_tokenizer_and_model(model_id, "flash_attention_2", torch_device)
        eos_token_id = model.config.eos_token_id  # type: ignore[attr-defined]

        # Same prompt for both requests
        user_messages = ["Write a random number:"]
        input_ids = get_generation_inputs(user_messages, tokenizer, for_continuous_batching=True)[0]

        # Use the context manager to add requests with different per-request kwargs
        generation_config = GenerationConfig(
            do_sample=True,
            temperature=max(temperatures) + 1,  # enables temperature warping
            top_k=max(top_ks) + 1,
            top_p=min(top_ps) - 0.01,
            max_new_tokens=max_new_tokens,
            eos_token_id=eos_token_id,
        )
        continuous_batching_config = ContinuousBatchingConfig(
            use_cuda_graph=use_cuda_graph,
            use_async_batching=use_async_batching,
            per_request_processors=True,
            return_logprobs=True,
        )
        manager = model.init_continuous_batching(
            generation_config=generation_config,
            continuous_batching_config=continuous_batching_config,
            q_padding_interval_size=16,  # allows for exact comparison between CB and regular generation
        )

        # Trick to have temperature, top-k, top-p ... without randomness: diable sampling after manager creation
        manager.generation_config.do_sample = False

        manager.start()
        try:
            # Request 0: low temperature (more deterministic)
            req0_id = manager.add_request(
                input_ids, max_new_tokens=max_new_tokens, temperature=temperatures[0], top_k=top_ks[0], top_p=top_ps[0]
            )
            # Request 1: high temperature (more random)
            req1_id = manager.add_request(
                input_ids, max_new_tokens=max_new_tokens, temperature=temperatures[1], top_k=top_ks[1], top_p=top_ps[1]
            )
            # Collect results
            results = {}
            while len(results) < 2:
                result = manager.get_result(timeout=1)
                if result is not None and result.is_finished():
                    results[result.request_id] = result
                elif not manager.is_running():
                    break
        finally:
            manager.stop(block=True)

        # Both requests should complete and have logprobs
        self.assertEqual(len(results), 2, f"Expected 2 results, got {len(results)}")
        self.assertGreater(len(results[req0_id].logprobs), 0)
        self.assertGreater(len(results[req1_id].logprobs), 0)
        # Also ensure the logprobs were not the same
        self.assertNotEqual(results[req0_id].logprobs, results[req1_id].logprobs)

        # Compare each request with regular generation
        # Build logits processor with do_sample=True (so temperature is included), then set do_sample=False for
        # deterministic generation, which is the same trick that CB uses
        delta = 2e-5 if use_cuda_graph else 1e-5
        for i, req_id in enumerate([req0_id, req1_id]):
            tokenizer, model = get_tokenizer_and_model(model_id, "flash_attention_2", torch_device)
            gen_config = GenerationConfig(
                do_sample=True,
                temperature=temperatures[i],
                top_k=top_ks[i],
                top_p=top_ps[i],
                max_new_tokens=max_new_tokens,
                eos_token_id=eos_token_id,
            )
            logits_processor = model._get_logits_processor(gen_config)
            gen_config.do_sample = False
            regular_generated_tokens, regular_logprobs = regular_generate(
                model=model,
                tokenizer=tokenizer,
                user_messages=user_messages,
                logits_processor=logits_processor,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                output_scores=True,
                eos_token_id=eos_token_id,
            )
            self.assertEqual(results[req_id].generated_tokens, regular_generated_tokens[0])
            for j, (cb_lp, exp_lp) in enumerate(zip(results[req_id].logprobs, regular_logprobs[0])):
                error_msg = f"Request {i}: logprob mismatch at position {j}: CB={cb_lp}, expected={exp_lp}"
                self.assertAlmostEqual(cb_lp, exp_lp, delta=delta, msg=error_msg)