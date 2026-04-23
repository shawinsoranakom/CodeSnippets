def _load_correct_tokenizer(
    tokenizer_name,
    model_max_length = None,
    padding_side = "right",
    token = None,
    trust_remote_code = False,
    cache_dir = "huggingface_tokenizers_cache",
    fix_tokenizer = True,
):
    if IS_COLAB_ENVIRONMENT:
        cache_dir = cache_dir
    elif IS_KAGGLE_ENVIRONMENT:
        # /tmp of Kaggle seems has a 80GB limit!
        # Let's utilize them
        cache_dir = os.path.join(KAGGLE_TMP, cache_dir)
    else:
        cache_dir = None

    # Try loading the slow tokenizer. If it fails, then try Fast only
    # Mainly to solve Deepseek models with no tokenizer.model file
    slow_tokenizer = None
    try:
        slow_tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_name,
            model_max_length = model_max_length,
            padding_side = padding_side,
            token = token,
            trust_remote_code = trust_remote_code,
            # Cannot just use use_fast = False as per https://twitter.com/danielhanchen/status/1789659394302718373
            use_fast = False,
            legacy = False,
            from_slow = True,
            cache_dir = cache_dir,
        )
    except:
        slow_tokenizer = None
        # print(
        #     f"Unsloth: {tokenizer_name} has no tokenizer.model file.\n"\
        #     "Just informing you about this - this is not a critical error."
        # )
    # Unsure why this occurs!
    if type(slow_tokenizer) is bool:
        slow_tokenizer = None

    fast_tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_name,
        model_max_length = model_max_length,
        padding_side = padding_side,
        token = token,
        trust_remote_code = trust_remote_code,
        cache_dir = cache_dir,
    )

    if not fix_tokenizer or tokenizer_name in IGNORED_TOKENIZER_NAMES:
        return fast_tokenizer
    # Ignore Mistral ones - they're a bit weird to handle!
    elif "mistral" in tokenizer_name.lower():
        return fast_tokenizer
    # Ignore Phi-4 ones as well
    elif "phi-4" in tokenizer_name.lower():
        return fast_tokenizer
    elif slow_tokenizer is not None:
        if hasattr(fast_tokenizer, "add_bos_token") and hasattr(
            slow_tokenizer, "add_bos_token"
        ):
            fast_tokenizer.add_bos_token = slow_tokenizer.add_bos_token
        if hasattr(fast_tokenizer, "add_eos_token") and hasattr(
            slow_tokenizer, "add_eos_token"
        ):
            fast_tokenizer.add_eos_token = slow_tokenizer.add_eos_token

        # Confirm if slow and fast are equivalent!
        if assert_same_tokenization(slow_tokenizer, fast_tokenizer):
            return fast_tokenizer
        else:
            logger.warning(
                f"Unsloth: Will load {tokenizer_name} as a legacy tokenizer."
            )
            return convert_to_fast_tokenizer(slow_tokenizer)
        pass
    else:
        return fast_tokenizer