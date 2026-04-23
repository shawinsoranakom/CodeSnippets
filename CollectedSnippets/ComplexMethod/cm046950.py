def sft_trainer_prepare_dataset(function_name, function):
    if (
        function_name != "_prepare_non_packed_dataloader"
        and function_name != "_prepare_dataset"
    ):
        return function

    fast_sft_prepare_dataset = RL_REPLACEMENTS.get("sft_prepare_dataset", None)
    if fast_sft_prepare_dataset is not None:
        params = inspect.signature(fast_sft_prepare_dataset).parameters.keys()
        params = ".*?".join(params)
        matched = re.match(
            r"[\s]{0,}def _prepare_dataset\(.*?" + params + r".*?\)",
            function,
            flags = re.MULTILINE | re.DOTALL,
        )
        if matched:
            # Use fast version!
            function = inspect.getsource(fast_sft_prepare_dataset)
            function = function.split("\n")
            function = "\n".join(" " * 4 + x for x in function)
            function = function.replace(
                "def sft_prepare_dataset", "def _prepare_dataset"
            )
            return function

    check_text = (
        "if 'skip_prepare_dataset' in locals() and skip_prepare_dataset:\n"
        "    return dataset\n"
        "if 'tokenizer'          not in locals(): tokenizer = processing_class\n"
        "if 'formatting_func'    not in locals(): raise RuntimeError('Unsloth: Please file a bug report - `formatting_func` does not exist!')\n"
        "if 'dataset_text_field' not in locals() and 'args' in locals(): dataset_text_field = args.dataset_text_field\n"
        "if 'dataset_text_field' not in locals(): dataset_text_field = None\n"
        "if formatting_func is None and dataset_text_field is None and 'prompt' in dataset[0] and 'completion' in dataset[0]:\n"
        "    test_text = (dataset[0]['prompt'] + dataset[0]['completion']) if (isinstance(dataset[0]['prompt'], str) and isinstance(dataset[0]['completion'], str)) else None\n"
        "elif formatting_func is None and dataset_text_field is not None:\n"
        "    test_text = dataset[0][dataset_text_field]\n"
        "elif formatting_func is not None:\n"
        "    test_text = formatting_func(dataset[0])[0]\n"
        "else:\n"
        "    test_text = None\n"
        "chat_template = getattr(tokenizer, 'chat_template', None)\n"
        "chat_template = '' if chat_template is None else chat_template\n"
        "has_bos_token_already = ((test_text is not None and test_text.startswith(tokenizer.bos_token)) or tokenizer.bos_token in chat_template) "
        "if getattr(tokenizer, 'bos_token', None) is not None else False\n"
        "if 'add_special_tokens' not in locals() and has_bos_token_already:\n"
        "    from functools import partial\n"
        "    tokenizer_call = tokenizer.__call__\n"
        "    tokenizer.__call__ = partial(tokenizer_call, add_special_tokens = False)\n"
        "    processing_class = tokenizer\n"
        "else:\n"
        "    tokenizer_call = None\n"
        "    add_special_tokens = False if has_bos_token_already else locals().get('add_special_tokens', False)\n"
    )

    check_text = check_text.split("\n")
    check_text = "\n".join(" " * 8 + x for x in check_text)
    check_text = check_text.rstrip() + "\n"

    # .*? matches first match. .+? matches final match.
    replacer = re.findall(
        r"def " + function_name + r"\(.*?\).*?\:\n",
        function,
        flags = re.MULTILINE | re.DOTALL,
    )
    if len(replacer) != 0:
        replacer = replacer[0]
        function = function.replace(replacer, replacer + check_text)

    # Return tokenizer's original state
    return_state = (
        "if tokenizer_call is not None: tokenizer.__call__ = tokenizer_call\n"
    )
    function = re.sub(
        r"\n([ ]{4,})(return .*?[\s]{0,})$",
        rf"\1{return_state}\1\2",
        function,
    )
    return function