def compare_all_settings(
    model: str,
    all_args: list[list[str]],
    all_envs: list[dict[str, str] | None],
    *,
    method: str = "generate",
    max_wait_seconds: float | None = None,
) -> None:
    """
    Launch API server with several different sets of arguments/environments
    and compare the results of the API calls with the first set of arguments.
    Args:
        model: The model to test.
        all_args: A list of argument lists to pass to the API server.
        all_envs: A list of environment dictionaries to pass to the API server.
    """

    trust_remote_code = False
    for args in all_args:
        if "--trust-remote-code" in args:
            trust_remote_code = True
            break

    tokenizer_mode = "auto"
    for args in all_args:
        if "--tokenizer-mode" in args:
            tokenizer_mode = args[args.index("--tokenizer-mode") + 1]
            break

    tokenizer = get_tokenizer(
        model,
        trust_remote_code=trust_remote_code,
        tokenizer_mode=tokenizer_mode,
    )

    can_force_load_format = True

    for args in all_args:
        if "--load-format" in args:
            can_force_load_format = False
            break

    prompt = "Hello, my name is"
    token_ids = tokenizer(prompt).input_ids
    ref_results: list = []
    for i, (args, env) in enumerate(zip(all_args, all_envs)):
        if can_force_load_format:
            # we are comparing the results and
            # usually we don't need real weights.
            # we force to use dummy weights by default,
            # and it should work for most of the cases.
            # if not, we can use VLLM_TEST_FORCE_LOAD_FORMAT
            # environment variable to force the load format,
            # e.g. in quantization tests.
            args = args + ["--load-format", envs.VLLM_TEST_FORCE_LOAD_FORMAT]
        compare_results: list = []
        results = ref_results if i == 0 else compare_results
        with RemoteOpenAIServer(
            model, args, env_dict=env, max_wait_seconds=max_wait_seconds
        ) as server:
            client = server.get_client()

            # test models list
            models = client.models.list()
            models = models.data
            served_model = models[0]
            results.append(
                {
                    "test": "models_list",
                    "id": served_model.id,
                    "root": served_model.root,
                }
            )

            if method == "generate":
                results += _test_completion(client, model, prompt, token_ids)
            elif method == "generate_close":
                results += _test_completion_close(client, model, prompt)
            elif method == "generate_chat":
                results += _test_chat(client, model, prompt)
            elif method == "generate_with_image":
                results += _test_image_text(
                    client,
                    model,
                    "https://vllm-public-assets.s3.us-west-2.amazonaws.com/vision_model_images/RGBA_comp.png",
                )
            elif method == "encode":
                results += _test_embeddings(client, model, prompt)
            else:
                raise ValueError(f"Unknown method: {method}")

            if i > 0:
                # if any setting fails, raise an error early
                ref_args = all_args[0]
                ref_envs = all_envs[0]
                compare_args = all_args[i]
                compare_envs = all_envs[i]
                for ref_result, compare_result in zip(ref_results, compare_results):
                    ref_result = copy.deepcopy(ref_result)
                    compare_result = copy.deepcopy(compare_result)
                    if "embedding" in ref_result and method == "encode":
                        sim = F.cosine_similarity(
                            torch.tensor(ref_result["embedding"]),
                            torch.tensor(compare_result["embedding"]),
                            dim=0,
                        )
                        assert sim >= 0.999, (
                            f"Embedding for {model=} are not the same.\n"
                            f"cosine_similarity={sim}\n"
                        )
                        del ref_result["embedding"]
                        del compare_result["embedding"]
                    assert ref_result == compare_result, (
                        f"Results for {model=} are not the same.\n"
                        f"{ref_args=} {ref_envs=}\n"
                        f"{compare_args=} {compare_envs=}\n"
                        f"{ref_result=}\n"
                        f"{compare_result=}\n"
                    )