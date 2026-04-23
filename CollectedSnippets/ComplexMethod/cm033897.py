def _parse_params(term, paramvals):
    """Safely split parameter term to preserve spaces"""

    # TODO: deprecate this method
    valid_keys = paramvals.keys()
    params = defaultdict(lambda: '')

    # TODO: check kv_parser to see if it can handle spaces this same way
    keys = []
    thiskey = 'key'  # initialize for 'lookup item'
    for idp, phrase in enumerate(term.split()):

        # update current key if used
        if '=' in phrase:
            for k in valid_keys:
                if ('%s=' % k) in phrase:
                    thiskey = k

        # if first term or key does not exist
        if idp == 0 or not params[thiskey]:
            params[thiskey] = phrase
            keys.append(thiskey)
        else:
            # append to existing key
            params[thiskey] += ' ' + phrase

    # return list of values
    return [params[x] for x in keys]