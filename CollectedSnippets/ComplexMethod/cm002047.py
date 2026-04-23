def get_clean_sequence(self, tokenizer, with_prefix_space=False, max_length=20, min_length=5) -> tuple[str, list]:
        # XXX The default common tokenizer tests assume that every ID is decodable on its own.
        # This assumption is invalid for Perceiver because single bytes might not be
        # valid utf-8 (byte 128 for instance).
        # Here we're overriding the smallest possible method to provide
        # a clean sequence without making the same assumption.

        toks = []
        for i in range(len(tokenizer)):
            try:
                tok = tokenizer.decode([i], clean_up_tokenization_spaces=False)
            except UnicodeDecodeError:
                pass
            toks.append((i, tok))

        toks = list(filter(lambda t: re.match(r"^[ a-zA-Z]+$", t[1]), toks))
        toks = list(filter(lambda t: [t[0]] == tokenizer.encode(t[1], add_special_tokens=False), toks))
        if max_length is not None and len(toks) > max_length:
            toks = toks[:max_length]
        if min_length is not None and len(toks) < min_length and len(toks) > 0:
            while len(toks) < min_length:
                toks = toks + toks
        # toks_str = [t[1] for t in toks]
        toks_ids = [t[0] for t in toks]

        # Ensure consistency
        output_txt = tokenizer.decode(toks_ids, clean_up_tokenization_spaces=False)
        if " " not in output_txt and len(toks_ids) > 1:
            output_txt = (
                tokenizer.decode([toks_ids[0]], clean_up_tokenization_spaces=False)
                + " "
                + tokenizer.decode(toks_ids[1:], clean_up_tokenization_spaces=False)
            )
        if with_prefix_space:
            output_txt = " " + output_txt
        output_ids = tokenizer.encode(output_txt, add_special_tokens=False)
        return output_txt, output_ids