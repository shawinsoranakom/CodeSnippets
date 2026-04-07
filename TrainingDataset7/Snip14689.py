def join_tokens(tokens, trim=False):
        message = "".join(tokens)
        if trim:
            message = trim_whitespace(message)
        return message