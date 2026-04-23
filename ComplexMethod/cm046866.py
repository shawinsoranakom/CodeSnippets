def get_ollama_eos_tokens(tokenizer, extra_eos_tokens = []):
    added_tokens_decoder = tokenizer.added_tokens_decoder.values()
    added_tokens_decoder = [str(x) for x in added_tokens_decoder]

    # Remove added_tokens_decoder duplicates
    added_tokens_decoder = list(set(added_tokens_decoder) - set(extra_eos_tokens))

    # Remove BOS
    if getattr(tokenizer, "bos_token", None) is not None:
        added_tokens_decoder = [x for x in added_tokens_decoder if x != tokenizer.bos_token]

    repeatted_tokens = []
    # Join all vocab
    joined_text = "\x01\x00".join(added_tokens_decoder)
    for token in added_tokens_decoder:
        n = len(token)
        repeatted_counts = joined_text.count(token[:n//2])
        # Try finding longer than 1/2 of the token in the rest
        # For eg <|reserved_special_token_0|>, <|reserved_special_token_1|>
        if repeatted_counts > 2:
            for j in range(n//2+1, n):
                if joined_text.count(token[:j]) < repeatted_counts:
                    j -= 1
                    # Remove repeatted tokens to reduce search space
                    joined_text = joined_text.replace(token[:j], "")
                    repeatted_tokens.append(token[:j])
                    break

    # Remove duplicates
    splitted = joined_text.split("\x01\x00")
    final_eos_tokens = [old for old, new in zip(added_tokens_decoder, splitted) if old == new]
    final_eos_tokens += extra_eos_tokens
    final_eos_tokens += repeatted_tokens

    # Remove new lines, spaces and HTML tags
    filtered_eos_tokens = []
    for token in final_eos_tokens:
        if   token.count("\n") == len(token): continue
        elif token.count("▁") == len(token): continue
        elif token.startswith("<") and len(token) <= 2: continue
        elif token.startswith("</") and len(token) == 3: continue
        filtered_eos_tokens.append(token)
    return filtered_eos_tokens