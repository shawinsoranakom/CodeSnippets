def JSONObject(
    s_and_end, strict, scan_once, object_hook, object_pairs_hook, memo=None, _w=WHITESPACE.match, _ws=WHITESPACE_STR
):
    """Parse a JSON object from a string and return the parsed object.

    Args:
        s_and_end (tuple): A tuple containing the input string to parse and the current index within the string.
        strict (bool): If `True`, enforces strict JSON string decoding rules.
            If `False`, allows literal control characters in the string. Defaults to `True`.
        scan_once (callable): A function to scan and parse JSON values from the input string.
        object_hook (callable): A function that, if specified, will be called with the parsed object as a dictionary.
        object_pairs_hook (callable): A function that, if specified, will be called with the parsed object as a list of pairs.
        memo (dict, optional): A dictionary used to memoize string keys for optimization. Defaults to None.
        _w (function): A regular expression matching function for whitespace. Defaults to WHITESPACE.match.
        _ws (str): A string containing whitespace characters. Defaults to WHITESPACE_STR.

    Returns:
        tuple or dict: A tuple containing the parsed object and the index of the character in the input string
        after the end of the object.
    """

    s, end = s_and_end
    pairs = []
    pairs_append = pairs.append
    # Backwards compatibility
    if memo is None:
        memo = {}
    memo_get = memo.setdefault
    # Use a slice to prevent IndexError from being raised, the following
    # check will raise a more specific ValueError if the string is empty
    nextchar = s[end : end + 1]
    # Normally we expect nextchar == '"'
    if nextchar != '"' and nextchar != "'":
        if nextchar in _ws:
            end = _w(s, end).end()
            nextchar = s[end : end + 1]
        # Trivial empty object
        if nextchar == "}":
            if object_pairs_hook is not None:
                result = object_pairs_hook(pairs)
                return result, end + 1
            pairs = {}
            if object_hook is not None:
                pairs = object_hook(pairs)
            return pairs, end + 1
        elif nextchar != '"':
            raise JSONDecodeError("Expecting property name enclosed in double quotes", s, end)
    end += 1
    while True:
        if end + 1 < len(s) and s[end] == nextchar and s[end + 1] == nextchar:
            # Handle the case where the next two characters are the same as nextchar
            key, end = scanstring(s, end + 2, strict, delimiter=nextchar * 3)
        else:
            # Handle the case where the next two characters are not the same as nextchar
            key, end = scanstring(s, end, strict, delimiter=nextchar)
        key = memo_get(key, key)
        # To skip some function call overhead we optimize the fast paths where
        # the JSON key separator is ": " or just ":".
        if s[end : end + 1] != ":":
            end = _w(s, end).end()
            if s[end : end + 1] != ":":
                raise JSONDecodeError("Expecting ':' delimiter", s, end)
        end += 1

        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end + 1).end()
        except IndexError:
            pass

        try:
            value, end = scan_once(s, end)
        except StopIteration as err:
            raise JSONDecodeError("Expecting value", s, err.value) from None
        pairs_append((key, value))
        try:
            nextchar = s[end]
            if nextchar in _ws:
                end = _w(s, end + 1).end()
                nextchar = s[end]
        except IndexError:
            nextchar = ""
        end += 1

        if nextchar == "}":
            break
        elif nextchar != ",":
            raise JSONDecodeError("Expecting ',' delimiter", s, end - 1)
        end = _w(s, end).end()
        nextchar = s[end : end + 1]
        end += 1
        if nextchar != '"':
            raise JSONDecodeError("Expecting property name enclosed in double quotes", s, end - 1)
    if object_pairs_hook is not None:
        result = object_pairs_hook(pairs)
        return result, end
    pairs = dict(pairs)
    if object_hook is not None:
        pairs = object_hook(pairs)
    return pairs, end