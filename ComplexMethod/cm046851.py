def assert_same_tokenization(slow_tokenizer, fast_tokenizer):
    # Get eos_token, bos_token etc
    if not hasattr(slow_tokenizer, "all_special_tokens"):
        return True
    dir_names = dir(slow_tokenizer)
    special_tokens = list(
        filter(
            None,
            (
                getattr(slow_tokenizer, x)
                for x in dir_names
                if x.endswith("_token") and x.count("_") == 1
            ),
        )
    )
    all_special_tokens = list(set(special_tokens + slow_tokenizer.all_special_tokens))

    # Remove replacement char for false positive
    replacement_char = b"\xc3\xaf\xc2\xbf\xc2\xbd".decode("utf-8")
    all_special_tokens = [x for x in all_special_tokens if x != replacement_char]

    # Check if chat template is enabled!
    check_chat_template1 = True
    check_chat_template2 = True
    check_chat_template3 = True

    """
    Weirdly Mistral tokenizers are actually correct??
    Ie below will actually load mistral v1 and v3 incorrectly!

    slow_chat_template = getattr(slow_tokenizer, "chat_template", None)
    fast_chat_template = getattr(fast_tokenizer, "chat_template", None)
    messages = [
        {"role": "user", "content": " What is 2+2? "},
        {"role": "assistant", "content": " It's 4. "},
    ]
    # Check the tokenizer's own chat template
    if slow_chat_template is not None and fast_chat_template is not None:
        check_chat_template1 = \
            slow_tokenizer.apply_chat_template(messages) == \
            fast_tokenizer.apply_chat_template(messages)
    pass

    # Check Mistral chat template without BOS / EOS
    slow_tokenizer.chat_template = mistral_template
    fast_tokenizer.chat_template = mistral_template
    check_chat_template2 = \
        slow_tokenizer.apply_chat_template(messages) == \
        fast_tokenizer.apply_chat_template(messages)
    pass

    # Check Llama chat template without BOS / EOS
    slow_tokenizer.chat_template = llama_template
    fast_tokenizer.chat_template = llama_template
    check_chat_template3 = \
        slow_tokenizer.apply_chat_template(messages) == \
        fast_tokenizer.apply_chat_template(messages)
    pass

    # Combine them all and revert chat templates
    slow_tokenizer.chat_template = slow_chat_template
    fast_tokenizer.chat_template = fast_chat_template
    """
    check_chat_template = (
        check_chat_template1 and check_chat_template2 and check_chat_template3
    )

    # Try special tokens
    try:
        string = (
            "\n".join(all_special_tokens)
            + "A quick brown fox jumps over the lazy dog!!\n\nHi</s>\n\n"
            + "".join(all_special_tokens)
        )
        check_special_tokens = (
            slow_tokenizer(string).input_ids == fast_tokenizer(string).input_ids
        )

        return check_chat_template and check_special_tokens
    except:
        # For eg see https://github.com/unslothai/unsloth/issues/292
        # Sometimes tokenizer has weird tokens, causing a combined tokenization to fail.
        # [TODO] We temporarily disable this for CodeLlama tokenizers
        if slow_tokenizer.__repr__().split("(", 1)[0] in IGNORED_TOKENIZER_CHECKING:
            return check_chat_template
        else:
            return False