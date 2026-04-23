def try_fix_tokenizer(tokenizer, prepend = True):
    if hasattr(tokenizer, "_tokenizer"):
        converted_tokenizer = tokenizer._tokenizer
    else:
        converted_tokenizer = convert_slow_tokenizer(tokenizer)

    tokenizer_string = converted_tokenizer.to_str()

    # Llama does _apple. Sometimes this is wrong!!
    prepend_text = '{"type":"Prepend","prepend":"▁"},'
    if not prepend and prepend_text in tokenizer_string:
        tokenizer_string = tokenizer_string.replace(prepend_text, "", 1)

    dir_names = dir(tokenizer)
    # Get eos_token, bos_token etc
    token_names = [x for x in dir_names if x.endswith("_token") and x.count("_") == 1]

    for token_name in token_names:
        token = getattr(tokenizer, token_name, None)
        if token is None:
            continue
        token_id = getattr(tokenizer, token_name + "_id", None)
        if token_id is None:
            continue

        # Locate the token's id mapping in the string
        find_text = f'"id":{token_id},"content":"'
        find_pos = tokenizer_string.find(find_text)
        if find_pos == -1:
            continue
        start = find_pos + len(find_text)
        end = tokenizer_string.find('",', start)
        if end == -1:
            continue

        bad_token = tokenizer_string[start:end]
        # Check if token is the actual same one - if not, edit it
        if bad_token != token:
            bad_text = f'{find_text}{bad_token}",'
            good_text = f'{find_text}{token}",'
            tokenizer_string = tokenizer_string.replace(bad_text, good_text, 1)

            # And replace vocab section
            bad_text = f'"{bad_token}":{token_id},'
            good_text = f'"{token}":{token_id},'
            tokenizer_string = tokenizer_string.replace(bad_text, good_text, 1)

    fixed_tokenizer = converted_tokenizer.from_str(tokenizer_string)
    return fixed_tokenizer