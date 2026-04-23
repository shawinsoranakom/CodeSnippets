def tokenize_line(self, line, *, target_token_count=None):
        if shared.opts.emphasis != "None":
            parsed = prompt_parser.parse_prompt_attention(line)
        else:
            parsed = [[line, 1.0]]

        tokenized = self.tokenize([text for text, _ in parsed])

        tokens = []
        multipliers = []

        for text_tokens, (text, weight) in zip(tokenized, parsed):
            if text == 'BREAK' and weight == -1:
                continue

            tokens += text_tokens
            multipliers += [weight] * len(text_tokens)

        tokens += [self.id_end]
        multipliers += [1.0]

        if target_token_count is not None:
            if len(tokens) < target_token_count:
                tokens += [self.id_pad] * (target_token_count - len(tokens))
                multipliers += [1.0] * (target_token_count - len(tokens))
            else:
                tokens = tokens[0:target_token_count]
                multipliers = multipliers[0:target_token_count]

        return tokens, multipliers