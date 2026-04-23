def make_rst(infile, outfile='Doc/library/token-list.inc',
             rstfile='Doc/library/token.rst'):
    tok_names, ERRORTOKEN, string_to_tok = load_tokens(infile)
    tok_to_string = {value: s for s, value in string_to_tok.items()}

    needs_handwritten_doc = set()

    names = []
    for value, name in enumerate(tok_names):
        if value in tok_to_string:
            assert name.isupper()
            names.append(f'   * - .. data:: {name}')
            names.append(f'     - ``"{tok_to_string[value]}"``')
        else:
            needs_handwritten_doc.add(name)

    has_handwritten_doc = set()
    with open(rstfile) as fileobj:
        tokendef_re = re.compile(r'.. data:: ([0-9A-Z_]+)\s*')
        for line in fileobj:
            if match := tokendef_re.fullmatch(line):
                has_handwritten_doc.add(match[1])

    # Exclude non-token constants in token.py
    has_handwritten_doc -= {'N_TOKENS', 'NT_OFFSET', 'EXACT_TOKEN_TYPES'}

    if needs_handwritten_doc != has_handwritten_doc:
        message_parts = [f'ERROR: {rstfile} does not document all tokens!']
        undocumented = needs_handwritten_doc - has_handwritten_doc
        extra = has_handwritten_doc - needs_handwritten_doc
        if undocumented:
            message_parts.append(f'Undocumented tokens: {undocumented}')
        if extra:
            message_parts.append(f'Documented nonexistent tokens: {extra}')
        exit('\n'.join(message_parts))

    if update_file(outfile, token_inc_template % '\n'.join(names)):
        print("%s regenerated from %s" % (outfile, infile))