def _parse_sub(source, state, verbose, nested):
    # parse an alternation: a|b|c

    items = []
    itemsappend = items.append
    sourcematch = source.match
    while True:
        itemsappend(_parse(source, state, verbose, nested + 1,
                           not nested and not items))
        if not sourcematch("|"):
            break
        if not nested:
            verbose = state.flags & SRE_FLAG_VERBOSE

    if len(items) == 1:
        return items[0]

    subpattern = SubPattern(state)

    # check if all items share a common prefix
    while True:
        prefix = None
        for item in items:
            if not item:
                break
            if prefix is None:
                prefix = item[0]
            elif item[0] != prefix:
                break
        else:
            # all subitems start with a common "prefix".
            # move it out of the branch
            for item in items:
                del item[0]
            subpattern.append(prefix)
            continue # check next one
        break

    # check if the branch can be replaced by a character set
    set = []
    for item in items:
        if len(item) != 1:
            break
        op, av = item[0]
        if op is LITERAL:
            set.append((op, av))
        elif op is IN and av[0][0] is not NEGATE:
            set.extend(av)
        else:
            break
    else:
        # we can store this as a character set instead of a
        # branch (the compiler may optimize this even more)
        subpattern.append((IN, _uniq(set)))
        return subpattern

    subpattern.append((BRANCH, (None, items)))
    return subpattern