def check_tokenizer(
    model,
    tokenizer,
    model_name = "unsloth/llama-2-7b-bnb-4bit",
    model_max_length = 4096,
    padding_side = "right",
    token = None,
    _reload = True,
):
    # Checks tokenizer for out of bounds ids.
    # Mainly a fix for https://huggingface.co/berkeley-nest/Starling-LM-7B-alpha
    # where <sep> had token id=32002.
    # See https://huggingface.co/berkeley-nest/Starling-LM-7B-alpha/discussions/25
    # Seems like the Fast tokenizer in Rust breaks things!

    # We ignore some of them!
    if tokenizer.__repr__().split("(", 1)[0] in IGNORED_TOKENIZER_CHECKING:
        return tokenizer

    max_embedding_size = model.model.embed_tokens.weight.shape[0]
    added_tokens_fast = tokenizer.added_tokens_decoder
    added_tokens_fast = {
        index: str(value) for index, value in added_tokens_fast.items()
    }
    sorted_keys = sorted(added_tokens_fast)
    added_tokens_fast = {key: added_tokens_fast[key] for key in sorted_keys}

    for j, index in enumerate(added_tokens_fast.keys()):
        if index >= max_embedding_size:
            bad_indices = list(added_tokens_fast.keys())[j:]
            bad_tokens = list(added_tokens_fast.values())[j:]
            if not _reload:
                # Try removing the token
                added_tokens = [str(x) for x in tokenizer.added_tokens_decoder.values()]
                special_tokens = tokenizer.special_tokens_map
                import itertools

                special_tokens = frozenset(
                    itertools.chain.from_iterable(
                        [x] if type(x) is str else x for x in special_tokens.values()
                    )
                )
                can_be_removed1 = [x for x in bad_tokens if x not in special_tokens]
                can_be_removed2 = [
                    x
                    for x in can_be_removed1
                    if x in tokenizer._added_tokens_encoder.keys()
                ]

                # Check of extra tokens can in fact we removed!
                can_be_removed = (len(can_be_removed1) == len(bad_tokens)) and (
                    len(can_be_removed2) == len(bad_tokens)
                )

                # Check if sep_token or other generic types
                remove_generic = False
                try_mapper = []
                if not can_be_removed:
                    names = dir(tokenizer)
                    names = (
                        x for x in names if x.endswith("_token") and x.count("_") == 1
                    )
                    generic_tokens = [(x, getattr(tokenizer, x, None)) for x in names]

                    try_removal = []
                    for token in bad_tokens:
                        for name_token, check_token in generic_tokens:
                            if check_token == token:
                                try_removal.append(token)
                                try_mapper.append(name_token)

                    # Recheck!
                    can_be_removed = len(try_removal) == len(bad_tokens)
                    if can_be_removed:
                        remove_generic = True
                    can_be_removed1 = bad_tokens

                if can_be_removed:
                    # Yes it can be fixed!
                    for j, bad_token in enumerate(can_be_removed1):
                        remove_id = tokenizer._added_tokens_encoder[bad_token]
                        del tokenizer._added_tokens_decoder[remove_id]
                        del tokenizer._added_tokens_encoder[bad_token]

                        if remove_generic and (try_removal[j] == bad_token):
                            # Remove sep token for example
                            setattr(tokenizer, try_mapper[j], None)
                            setattr(tokenizer, try_mapper[j] + "_id", None)
                    # Confirm 1 more time!
                    if max(tokenizer.added_tokens_decoder.keys()) < max_embedding_size:
                        logger.warning_once(
                            f"Unsloth loaded a broken tokenizer `{model_name}`, but managed to repair it!\n"
                            f"Tokens {bad_tokens} with ids {bad_indices} exceeds the max vocab size of {max_embedding_size}.\n"
                            "We removed these bad tokens. If you think this is incorrect, fix your tokenizer first."
                        )
                        return convert_to_fast_tokenizer(tokenizer)

                # :( Failure
                raise RuntimeError(
                    f"Unsloth tried to load `{model_name}`, but cannot succeed.\n"
                    f"Tokens {bad_tokens} with ids {bad_indices} exceeds the max vocab size of {max_embedding_size}.\n"
                    f"Fix your tokenizer since it'll perform out of bounds memory accesses."
                )

            if IS_COLAB_ENVIRONMENT or IS_KAGGLE_ENVIRONMENT:
                cache_dir = "huggingface_tokenizers_cache"
            else:
                cache_dir = None

            # Sometimes slow tokenizer does not work like Deepseek
            try:
                # Try slow tokenizer which can fix things!
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    model_max_length = model_max_length,
                    padding_side = padding_side,
                    token = token,
                    # Cannot just use use_fast = False as per https://twitter.com/danielhanchen/status/1789659394302718373
                    use_fast = False,
                    legacy = False,
                    from_slow = True,
                    cache_dir = cache_dir,
                )
                return check_tokenizer(
                    model = model,
                    tokenizer = tokenizer,
                    model_name = model_name,
                    model_max_length = model_max_length,
                    padding_side = padding_side,
                    token = token,
                    _reload = False,
                )
                break
            except:
                # Tokenizer has out of bounds issues and we can't
                # load the slow tokenizer version :(
                logger.warning_once(
                    "Unsloth: Tokenizer is most likely buggy, and Unsloth failed to repair it.\n"
                    "It will still work, but beware of out of bounds memory accesses.\n"
                    "Please file an issue on the model owner's repo about this issue."
                )
                return tokenizer
    return convert_to_fast_tokenizer(tokenizer)