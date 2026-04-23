def normalize_domain(domain):
    """Returns a normalized version of ``domain_expr``, where all implicit '&' operators
       have been made explicit. One property of normalized domain expressions is that they
       can be easily combined together as if they were single domain components.
    """
    warnings.warn("Since 19.0, use odoo.fields.Domain", DeprecationWarning)
    if isinstance(domain, orm_domains.Domain):
        # already normalized
        return list(domain)
    assert isinstance(domain, (list, tuple)), "Domains to normalize must have a 'domain' form: a list or tuple of domain components"
    if not domain:
        return [TRUE_LEAF]
    result = []
    expected = 1                            # expected number of expressions
    op_arity = {NOT_OPERATOR: 1, AND_OPERATOR: 2, OR_OPERATOR: 2}
    for token in domain:
        if expected == 0:                   # more than expected, like in [A, B]
            result[0:0] = [AND_OPERATOR]             # put an extra '&' in front
            expected = 1
        if isinstance(token, (list, tuple)):  # domain term
            expected -= 1
            if len(token) == 3 and token[1] in ('any', 'not any') and not isinstance(token[2], (Query, SQL)):
                token = (token[0], token[1], normalize_domain(token[2]))
            else:
                token = tuple(token)
        else:
            expected += op_arity.get(token, 0) - 1
        result.append(token)
    if expected:
        raise ValueError(f'Domain {domain} is syntactically not correct.')
    return result