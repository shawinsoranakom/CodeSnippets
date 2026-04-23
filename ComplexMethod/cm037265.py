def _reduced_vocabulary(tokenizer: TokenizerLike) -> dict[bytes, list[int]]:
    """Create a map from vocabulary tokens to lists of equivalent token ids.

    Returns:
        A Dict of token string -> equivalent token ids
    """
    eos_token_id = tokenizer.eos_token_id

    unicode_to_bytes = {
        v: k for k, v in convert_slow_tokenizer.bytes_to_unicode().items()
    }

    def convert_token_to_string(token: str) -> str:
        string = tokenizer.convert_tokens_to_string([token])

        # A hack to handle missing spaces to HF's Llama tokenizers
        if (
            type(token) is str
            and token.startswith(file_utils.SPIECE_UNDERLINE)
            or token == "<0x20>"
        ):
            return " " + string

        return string

    vocabulary: dict[bytes, list[int]] = {}
    empty_token_ids: list[int] = []
    for token, token_idx in tokenizer.get_vocab().items():
        if token in tokenizer.all_special_tokens:
            continue

        token_str = convert_token_to_string(token)
        if token_str:
            if isinstance(token, (bytes, bytearray)):
                # For BPE tokenizers where tokens are stored as bytes.

                # safe to ignore since token_str is of type (bytearray, bytes)
                # by this point.
                token_bytes = bytes(token_str)  # type: ignore[arg-type]

            elif (token_str == "\ufffd" and token != "\ufffd") or (
                "\ufffd" in token_str and not re_replacement_seq.match(token_str)
            ):
                # Handle tokens with invalid UTF-8 sequences.
                if re_llama_byte_token.match(token):
                    # Llama-like tokenizers use <0xXX> for incomplete sequences.
                    token_bytes = bytes([int(token[3:5], 16)])
                else:
                    # GPT2 tokenizers: map each byte back using unicode_to_bytes
                    byte_vals = [unicode_to_bytes.get(c) for c in token]
                    if None in byte_vals:
                        raise RuntimeError(
                            f"Cannot convert token `{token}`"
                            f" ({token_idx}) to bytes: {token_str}"
                        )
                    # safe to ignore, since if None in byte_vals,
                    # an error is thrown.
                    token_bytes = bytes(byte_vals)  # type: ignore[arg-type]
            else:
                token_bytes = token_str.encode("utf-8")

            if token_idx != eos_token_id:
                vocabulary.setdefault(token_bytes, []).append(token_idx)
        else:
            empty_token_ids.append(token_idx)

    return vocabulary