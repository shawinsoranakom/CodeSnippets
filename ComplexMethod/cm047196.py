def prettify_domain(domain, pre_indent=0):
    """
    Pretty-format a domain into a string by separating each leaf on a
    separated line and by including some indentation. Works with ``any``
    and ``not any`` too. The domain must be normalized.

    :param list domain: a normalized domain
    :param int pre_indent: (optinal) a starting indentation level
    :return: the domain prettified
    :rtype: str
    """

    # The ``stack`` is a stack of layers, each layer accumulates the
    # ``terms`` (leaves/operators) that share a same indentation
    # level (the depth of the layer inside the stack). ``left_count``
    # tracks how many terms should still appear on each layer before the
    # layer is considered complete.
    #
    # When a layer is completed, it is removed from the stack and
    # commited, i.e. its terms added to the ``commits`` list along with
    # the indentation for those terms.
    #
    # When a new operator is added to the layer terms, the current layer
    # is commited (but not removed from the stack if there are still
    # some terms that must be added) and a new (empty) layer is added on
    # top of the stack.
    #
    # When the domain has been fully iterated, the commits are used to
    # craft the final string. All terms are indented according to their
    # commit indentation level and separated by a new line.

    warnings.warn("Since 19.0, prettify_domain is deprecated", DeprecationWarning)
    stack = [{'left_count': 1, 'terms': []}]
    commits = []

    for term in domain:
        top = stack[-1]

        if term in DOMAIN_OPERATORS:
            # when a same operator appears twice in a row, we want to
            # include the second one on the same line as the former one
            if (not top['terms'] and commits
                and (commits[-1]['terms'] or [''])[-1].startswith(repr(term))):
                commits[-1]['terms'][-1] += f", {term!r}"  # hack
                top['left_count'] += 0 if term == NOT_OPERATOR else 1
            else:
                commits.append({
                    'indent': len(stack) - 1,
                    'terms': top['terms'] + [repr(term)]
                })
                top['terms'] = []
                top['left_count'] -= 1
                stack.append({
                    'left_count': 1 if term == NOT_OPERATOR else 2,
                    'terms': [],
                })
                top = stack[-1]
        elif term[1] in ('any', 'not any'):
            top['terms'].append('({!r}, {!r}, {})'.format(
                term[0], term[1], prettify_domain(term[2], pre_indent + len(stack) - 1)))
            top['left_count'] -= 1
        else:
            top['terms'].append(repr(term))
            top['left_count'] -= 1

        if not top['left_count']:
            commits.append({
                'indent': len(stack) - 1,
                'terms': top['terms']
            })
            stack.pop()

    return '[{}]'.format(
        f",\n{'    ' * pre_indent}".join([
            f"{'    ' * commit['indent']}{term}"
            for commit in commits
            for term in commit['terms']
        ])
    )