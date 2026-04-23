def extract_formula_terms(formula):
    """Extract strings in a spreadsheet formula which are arguments to '_t' functions

        >>> extract_formula_terms('=_t("Hello") + _t("Raoul")')
        ["Hello", "Raoul"]
    """
    tokens = generate_tokens(io.StringIO(formula).readline)
    tokens = (token for token in tokens if token.type not in {NEWLINE, INDENT, DEDENT})
    for t1 in tokens:
        if t1.string != '_t':
            continue
        t2 = next(tokens, None)
        if t2 and t2.string == '(':
            t3 = next(tokens, None)
            t4 = next(tokens, None)
            if t4 and t4.string == ')' and t3 and t3.type == STRING:
                yield t3.string[1:][:-1]