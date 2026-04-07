def __init__(self, tokens):
        # Turn 'is','not' and 'not','in' into single tokens.
        num_tokens = len(tokens)
        mapped_tokens = []
        i = 0
        while i < num_tokens:
            token = tokens[i]
            if token == "is" and i + 1 < num_tokens and tokens[i + 1] == "not":
                token = "is not"
                i += 1  # skip 'not'
            elif token == "not" and i + 1 < num_tokens and tokens[i + 1] == "in":
                token = "not in"
                i += 1  # skip 'in'
            mapped_tokens.append(self.translate_token(token))
            i += 1

        self.tokens = mapped_tokens
        self.pos = 0
        self.current_token = self.next_token()