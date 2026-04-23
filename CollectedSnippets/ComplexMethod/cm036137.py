def test_mamba_prefix_cache(monkeypatch: pytest.MonkeyPatch):
    run_ref_mamba_state_in_subprocess()
    apply_patch(monkeypatch)
    prompt_dataset = datasets.load_dataset("heheda/a_long_article")
    full_prompt = prompt_dataset["train"][0]["text"]
    tests = {
        "accept_1": TestConfig(
            num_prompt_tokens=554,
            num_generated_tokens=20,
            num_accepted_tokens=1,
            step_actions=[
                StepAction(0, 554, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(554, 4, [], (-1, -1), (-1, -1)),
                StepAction(555, 4, [1, 1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(556, 4, [], (-1, -1), (-1, -1)),
                StepAction(557, 4, [], (0, 1), (-1, -1)),
                StepAction(558, 4, [], (-1, -1), (-1, -1)),
                StepAction(559, 4, [], (-1, -1), (1, 0)),
                StepAction(560, 4, [], (-1, -1), (-1, -1)),
                StepAction(561, 4, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        # test case 2.1: no hit, accept 2 tokens
        "accept_2_1": TestConfig(
            num_prompt_tokens=554,
            num_generated_tokens=20,
            num_accepted_tokens=2,
            step_actions=[
                StepAction(0, 554, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(554, 4, [], (-1, -1), (-1, -1)),
                StepAction(556, 4, [1, 1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(558, 4, [], (1, 1), (2, 0)),
                StepAction(560, 4, [], (-1, -1), (-1, -1)),
                StepAction(562, 4, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        # test case 2.2: no hit, accept 2 tokens
        "accept_2_2": TestConfig(
            num_prompt_tokens=555,
            num_generated_tokens=20,
            num_accepted_tokens=2,
            step_actions=[
                StepAction(0, 555, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(555, 4, [], (-1, -1), (-1, -1)),
                StepAction(557, 4, [1, 1, 1, 1, 1], (1, 1), (-1, -1)),
                StepAction(559, 4, [], (-1, -1), (1, 0)),
                StepAction(561, 4, [], (-1, -1), (-1, -1)),
                StepAction(563, 4, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        "accept_3_1": TestConfig(
            num_prompt_tokens=553,
            num_generated_tokens=20,
            num_accepted_tokens=3,
            step_actions=[
                StepAction(0, 553, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(553, 4, [], (-1, -1), (-1, -1)),
                StepAction(556, 4, [1, 1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(559, 4, [], (2, 1), (1, 0)),
                StepAction(562, 4, [], (-1, -1), (-1, -1)),
                StepAction(565, 4, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        "accept_3_2": TestConfig(
            num_prompt_tokens=554,
            num_generated_tokens=20,
            num_accepted_tokens=3,
            step_actions=[
                StepAction(0, 554, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(554, 4, [], (-1, -1), (-1, -1)),
                StepAction(557, 4, [1, 1, 1, 1, 1], (2, 1), (3, 0)),
                StepAction(560, 4, [], (-1, -1), (-1, -1)),
                StepAction(563, 4, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        "accept_3_3": TestConfig(
            num_prompt_tokens=555,
            num_generated_tokens=20,
            num_accepted_tokens=3,
            step_actions=[
                StepAction(0, 555, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(555, 4, [], (-1, -1), (-1, -1)),
                StepAction(558, 4, [1, 1, 1, 1, 1], (2, 1), (2, 0)),
                StepAction(561, 4, [], (-1, -1), (-1, -1)),
                StepAction(564, 4, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        "accept_4_1": TestConfig(
            num_prompt_tokens=553,
            num_generated_tokens=20,
            num_accepted_tokens=4,
            step_actions=[
                StepAction(0, 553, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(553, 4, [], (-1, -1), (-1, -1)),
                StepAction(557, 4, [1, 1, 1, 1, 1], (3, 1), (3, 0)),
                StepAction(561, 4, [], (-1, -1), (-1, -1)),
                StepAction(565, 4, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        "accept_4_2": TestConfig(
            num_prompt_tokens=554,
            num_generated_tokens=25,
            num_accepted_tokens=4,
            step_actions=[
                StepAction(0, 554, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(554, 4, [], (-1, -1), (-1, -1)),
                StepAction(558, 4, [1, 1, 1, 1, 1], (3, 1), (2, 0)),
                StepAction(562, 4, [], (-1, -1), (-1, -1)),
                StepAction(566, 4, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        "accept_4_3": TestConfig(
            num_prompt_tokens=555,
            num_generated_tokens=25,
            num_accepted_tokens=4,
            step_actions=[
                StepAction(0, 555, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(555, 4, [], (-1, -1), (-1, -1)),
                StepAction(559, 4, [1, 1, 1, 1, 1], (3, 1), (1, 0)),
                StepAction(563, 4, [], (-1, -1), (-1, -1)),
                StepAction(567, 4, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        "accept_4_4": TestConfig(
            num_prompt_tokens=556,
            num_generated_tokens=25,
            num_accepted_tokens=4,
            step_actions=[
                StepAction(0, 556, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(556, 4, [], (-1, -1), (3, 0)),
                StepAction(560, 4, [1, 1, 1, 1, 1], (0, 1), (-1, -1)),
                StepAction(564, 4, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        "prompt_block_size": TestConfig(
            num_prompt_tokens=560,
            num_generated_tokens=10,
            num_accepted_tokens=4,
            step_actions=[
                StepAction(0, 560, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(560, 4, [1, 1, 1, 1, 1], (0, 1), (-1, -1)),
            ],
        ),
        "prompt_2_block_size": TestConfig(
            num_prompt_tokens=560 * 2,
            num_generated_tokens=10,
            num_accepted_tokens=4,
            step_actions=[
                StepAction(0, 560, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(560, 560, [1, 1, 1, 1, 1], (0, 1), (-1, -1)),
                StepAction(560 * 2, 4, [0, 1, 1, 1, 1, 1], (1, 2), (-1, -1)),
            ],
        ),
        "prompt_2_block_size_10": TestConfig(
            num_prompt_tokens=560 * 2 + 10,
            num_generated_tokens=10,
            num_accepted_tokens=4,
            step_actions=[
                StepAction(0, 560, [1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(560, 570, [1, 0, 1, 1, 1, 1], (0, 2), (-1, -1)),
                StepAction(560 * 2 + 10, 4, [0, 0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        "prompt_3_block_size": TestConfig(
            num_prompt_tokens=560 * 3,
            num_generated_tokens=10,
            num_accepted_tokens=4,
            step_actions=[
                StepAction(0, 560 * 2, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(560 * 2, 560, [0, 1, 1, 1, 1, 1], (1, 2), (-1, -1)),
                StepAction(560 * 3, 4, [0, 0, 1, 1, 1, 1, 1], (2, 3), (-1, -1)),
            ],
        ),
        "prompt_3_block_size_10": TestConfig(
            num_prompt_tokens=560 * 3 + 10,
            num_generated_tokens=10,
            num_accepted_tokens=4,
            step_actions=[
                StepAction(0, 560 * 2, [0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(560 * 2, 570, [0, 1, 0, 1, 1, 1, 1], (1, 3), (-1, -1)),
                StepAction(560 * 3 + 10, 4, [0, 0, 0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
            ],
        ),
        "prompt_10_block_size": TestConfig(
            num_prompt_tokens=560 * 10,
            num_generated_tokens=10,
            num_accepted_tokens=4,
            step_actions=[
                StepAction(0, 560 * 5, [0, 0, 0, 0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(
                    560 * 5,
                    560 * 4,
                    [0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1],
                    (4, 8),
                    (-1, -1),
                ),
                StepAction(
                    560 * 9,
                    560,
                    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
                    (8, 9),
                    (-1, -1),
                ),
                StepAction(
                    560 * 10,
                    4,
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
                    (9, 10),
                    (-1, -1),
                ),
            ],
        ),
        "prompt_10_block_size_10": TestConfig(
            num_prompt_tokens=560 * 10 + 10,
            num_generated_tokens=10,
            num_accepted_tokens=4,
            step_actions=[
                StepAction(0, 560 * 5, [0, 0, 0, 0, 1, 1, 1, 1], (-1, -1), (-1, -1)),
                StepAction(
                    560 * 5,
                    560 * 4,
                    [0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1],
                    (4, 8),
                    (-1, -1),
                ),
                StepAction(
                    560 * 9,
                    560 + 10,
                    [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1],
                    (8, 10),
                    (-1, -1),
                ),
            ],
        ),
    }

    engine = LLM(
        model=MODEL,
        enable_prefix_caching=True,
        block_size=BLOCK_SIZE,
        mamba_cache_mode="align",
        speculative_config={
            "method": "qwen3_next_mtp",
            "num_speculative_tokens": num_speculative_tokens,
        },
        max_num_batched_tokens=3072,
        hf_overrides={"num_hidden_layers": NUM_HIDDEN_LAYERS},
        seed=42,
    )
    global prompt_token_ids
    prompt_token_ids = engine.get_tokenizer().encode(full_prompt)
    print(f"Token IDs length: {len(prompt_token_ids)}")
    for test_case_name, test_config in tests.items():
        print(f"Running test case: {test_case_name}")
        num_generated_tokens = test_config.num_generated_tokens
        num_prompt_tokens = test_config.num_prompt_tokens
        global num_accepted_tokens
        num_accepted_tokens = test_config.num_accepted_tokens
        sampling_params = SamplingParams(
            temperature=0.0, max_tokens=num_generated_tokens
        )
        global cur_step_action_idx
        cur_step_action_idx = 0
        for step_action_prev, step_action_next in zip(
            test_config.step_actions[:-1], test_config.step_actions[1:]
        ):
            if (
                step_action_next.kv_cache_block_ids is not None
                and len(step_action_next.kv_cache_block_ids) == 0
            ):
                prev_block_ids = step_action_prev.kv_cache_block_ids
                if prev_block_ids is not None:
                    step_action_next.kv_cache_block_ids = prev_block_ids.copy()
        global step_actions
        step_actions = test_config.step_actions
        _ = engine.generate(
            [TokensPrompt(prompt_token_ids=prompt_token_ids[:num_prompt_tokens])],
            sampling_params,
        )
        assert engine.llm_engine.engine_core.engine_core.scheduler.reset_prefix_cache()
        print(f"End test case: {test_case_name}")
        keys_to_check = [
            (action.postprocess_copy_idx[1] + 1) * BLOCK_SIZE
            for action in test_config.step_actions
            if action.postprocess_copy_idx and action.postprocess_copy_idx[0] != -1
        ]
        mamba_state_ref = torch.load("mamba_kv_cache_dict_ref.pth")
        check_mamba_state_equal(mamba_state_ref, mamba_kv_cache_dict, keys_to_check)
        mamba_kv_cache_dict.clear()
    del engine
    torch.accelerator.empty_cache()
    cleanup_dist_env_and_memory()