def get_chat_template(
    tokenizer,
    chat_template = "chatml",
    mapping = {"role" : "role", "content" : "content", "user" : "user", "assistant" : "assistant"},
    map_eos_token = True,
    system_message = None,
):
    assert(type(map_eos_token) is bool)
    old_tokenizer = tokenizer

    IS_GEMMA = False
    if tokenizer.__class__.__name__.startswith("Gemma"):
        if chat_template == "chatml": chat_template = "gemma_chatml"
        IS_GEMMA = True

    # We add a check for Llama-3
    # if chat_template == "llama-3":
    #     tokenizer._using_llama3_template = True
    # else:
    #     llama3_tokens = set(["<|end_header_id|>", "<|eot_id|>", "<|start_header_id|>"])
    #     check_llama3_tokens = llama3_tokens & set(str(x) for x in tokenizer.added_tokens_decoder.values())
    #     if len(check_llama3_tokens) == len(llama3_tokens):
    #         tokenizer._using_llama3_template = True
    #     pass
    # pass

    # We first check if the tokenizer is a fast one. If not, we cannot convert this!
    is_fast_tokenizer = getattr(tokenizer, "is_fast", False)
    old_padding_side = tokenizer.padding_side

    same_padding_token = False
    type_chat_template = None

    if type(chat_template) in (list, tuple,):
        # For changing system message later
        # Since it's not supported yet, we will raise an error first!
        type_chat_template = chat_template[0].lower()
        chat_template, stop_word = chat_template
        assert(type(chat_template) is str)
        assert(type(stop_word) is str)
        ollama_modelfile = None

    elif type(chat_template) is str:
        # For changing system message later
        type_chat_template = chat_template.lower()

        chat_template, stop_word, yes_map_eos_token, ollama_modelfile = CHAT_TEMPLATES[chat_template]

        # Check mapping to eos_token
        if not map_eos_token and yes_map_eos_token: map_eos_token = True
        if not yes_map_eos_token and map_eos_token: map_eos_token = False

        if type(stop_word) in (list, tuple,):
            token_mapping, stop_word = stop_word
            assert(type(token_mapping) is dict)
        else:
            token_mapping = None

        assert(type(stop_word) is str)

        # Check fast tokenizer
        if not is_fast_tokenizer:
            pass
            # print(
            #     "Unsloth: Not a fast tokenizer, so can't process it as of yet :(\n"\
            #     "Please log a Github issue if you want this as a new feature!\n"\
            #     "Your chat template will still work, but it won't add or edit tokens."
            # )

        elif token_mapping is not None:
            # token_mapping = {"<start_of_turn>" : "<|im_start|>", "<end_of_turn>" : "<|im_end|>"}
            # For Gemma :)

            string_vocab = tokenizer._tokenizer.to_str()

            skipped = 0
            for old_token, new_token in token_mapping.items():
                old_count = string_vocab.count(f'"{old_token}"')
                new_count = string_vocab.count(f'"{new_token}"')
                if new_count != 0:
                    print(f"{new_token} is already a token. Skipping.")
                    skipped += 1
                elif old_count == 0:
                    raise RuntimeError(f"{old_token} was not part of the tokenizer!")
                else:
                    string_vocab = string_vocab.replace(f'"{old_token}"', f'"{new_token}"')
                pass
            pass

            if map_eos_token and (not stop_word in token_mapping.values()):
                # Do not map 107 = <|im_end|> and 1 = <|im_end|>. This will reduce the vocab size by 1
                logger.warning_once(f"Unsloth: Will map {stop_word} to EOS = {tokenizer.eos_token}.")
                string_vocab = string_vocab.replace(tokenizer.eos_token, stop_word)
            pass

            if skipped != len(token_mapping):
                new_tokenizer = tokenizer._tokenizer.from_str(string_vocab)

                # Careful on pad_token
                old_pad_token = tokenizer.pad_token
                if old_pad_token == tokenizer.eos_token:
                    old_pad_token = stop_word
                    same_padding_token = True
                pass

                if map_eos_token:
                    new_tokenizer = tokenizer.__class__(
                        tokenizer_object = new_tokenizer,
                        eos_token = stop_word,
                        pad_token = old_pad_token,
                    )
                else:
                    new_tokenizer = tokenizer.__class__(
                        tokenizer_object = new_tokenizer,
                        pad_token = old_pad_token,
                    )
                pass

                # Must fix the sentence piece tokenizer since there's no tokenizer.model file!
                tokenizer = fix_sentencepiece_tokenizer(tokenizer, new_tokenizer, token_mapping,)
            else:
                pass

        elif map_eos_token and (stop_word != "eos_token"):
            logger.warning_once(f"Unsloth: Will map {stop_word} to EOS = {tokenizer.eos_token}.")

            # Replaces the old EOS token with a new one.
            # Useful for ChatML <|im_end|> for example.
            # Usually we train 2 more tokens <|im_start|> and <|im_end|>
            # But training the lm_head and embeddings are slow!
            # This is a HACK!
            # Idea from https://huggingface.co/cognitivecomputations/dolphin-2.6-mistral-7b-dpo-laser

            old_bos_token = getattr(tokenizer, "bos_token", None)
            old_eos_token = getattr(tokenizer, "eos_token", None)
            old_pad_token = getattr(tokenizer, "pad_token", None)
            old_unk_token = getattr(tokenizer, "unk_token", None)

            string_vocab = tokenizer._tokenizer.to_str()
            # First check if new stop_word is in the tokenizer
            if stop_word in string_vocab:
                # We shall swap them around
                temporary_stop_token = "<|:__TEMP//STOP//TOKEN__:|>"
                string_vocab = string_vocab.replace(old_eos_token, temporary_stop_token)
                string_vocab = string_vocab.replace(stop_word, old_eos_token)
                string_vocab = string_vocab.replace(temporary_stop_token, stop_word)
            else:
                string_vocab = string_vocab.replace(old_eos_token, stop_word)
            pass
            new_tokenizer = tokenizer._tokenizer.from_str(string_vocab)

            # Careful on pad_token
            if old_pad_token == old_eos_token:
                old_pad_token = stop_word
                same_padding_token = True
            pass

            new_tokenizer = tokenizer.__class__(
                tokenizer_object = new_tokenizer,
                bos_token = old_bos_token,
                eos_token = stop_word,
                unk_token = old_unk_token,
                pad_token = old_pad_token,
            )

            # Must fix the sentence piece tokenizer since there's no tokenizer.model file!
            token_mapping = { old_eos_token : stop_word, }
            tokenizer = fix_sentencepiece_tokenizer(tokenizer, new_tokenizer, token_mapping,)
        pass

    else:
        raise TypeError(
            f"Unsloth: `chat_template` must be a tuple of (your_template, eos_token,) or one of\n"\
            f"{CHAT_TEMPLATES.keys()}"
        )

    # Careful on Gemma
    # bos_token is a must or else losses become too high
    if IS_GEMMA and not chat_template.startswith(("{{ bos_token }}", "{{- bos_token }}")):
        chat_template = "{{ bos_token }}" + chat_template

    # For ShareGPT role -> from and content -> value
    new_chat_template = chat_template\
        .replace("'role'",      "'" + mapping["role"]      + "'")\
        .replace("'content'",   "'" + mapping["content"]   + "'")\
        .replace("'user'",      "'" + mapping["user"]      + "'")\
        .replace("'assistant'", "'" + mapping["assistant"] + "'")

    _, tokenizer = patch_tokenizer(model = None, tokenizer = tokenizer)
    tokenizer.padding_side = old_padding_side

    # If not normal HF, we add a check to make old templates work
    if mapping != {"role" : "role", "content" : "content", "user" : "user", "assistant" : "assistant"}:
        chat_template = \
            "{% if 'role' in messages[0] %}" + \
            chat_template + \
            "{% else %}" + \
            new_chat_template + \
            "{% endif %}"
    else:
        chat_template = new_chat_template

    chat_template, system_message = _change_system_message(chat_template, type_chat_template, system_message)

    tokenizer.chat_template = chat_template

    # Also fix up other tokens
    old_pad_token = getattr(old_tokenizer, "pad_token", None)
    old_bos_token = getattr(old_tokenizer, "bos_token", None)
    old_unk_token = getattr(old_tokenizer, "unk_token", None)
    new_pad_token = getattr(tokenizer,     "pad_token", None)
    new_bos_token = getattr(tokenizer,     "bos_token", None)
    new_unk_token = getattr(tokenizer,     "unk_token", None)
    if old_bos_token != new_bos_token: tokenizer.bos_token = old_bos_token
    if old_unk_token != new_unk_token: tokenizer.unk_token = old_unk_token
    if not same_padding_token:
        if old_pad_token != new_pad_token: tokenizer.pad_token = old_pad_token

    # stopping_criteria = create_stopping_criteria(tokenizer, stop_word)

    # Patch saving functions
    tokenizer = patch_saving_functions(tokenizer)

    # Add Ollama
    tokenizer._ollama_modelfile = ollama_modelfile
    tokenizer._system_message   = system_message
    return tokenizer