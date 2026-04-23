def source_synopsis(file):
    """Return the one-line summary of a file object, if present"""

    string = ''
    try:
        tokens = tokenize.generate_tokens(file.readline)
        for tok_type, tok_string, _, _, _ in tokens:
            if tok_type == tokenize.STRING:
                string += tok_string
            elif tok_type == tokenize.NEWLINE:
                with warnings.catch_warnings():
                    # Ignore the "invalid escape sequence" warning.
                    warnings.simplefilter("ignore", SyntaxWarning)
                    docstring = ast.literal_eval(string)
                if not isinstance(docstring, str):
                    return None
                return docstring.strip().split('\n')[0].strip()
            elif tok_type == tokenize.OP and tok_string in ('(', ')'):
                string += tok_string
            elif tok_type not in (tokenize.COMMENT, tokenize.NL, tokenize.ENCODING):
                return None
    except (tokenize.TokenError, UnicodeDecodeError, SyntaxError):
        return None
    return None