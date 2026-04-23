def determine_valid_prefixes():
        # Try all lengths until we find a length that has zero valid
        # prefixes.  This will miss the case where for example there
        # are no valid 3 character prefixes, but there are valid 4
        # character prefixes.  That seems unlikely.

        single_char_valid_prefixes = set()

        # Find all of the single character string prefixes. Just get
        # the lowercase version, we'll deal with combinations of upper
        # and lower case later.  I'm using this logic just in case
        # some uppercase-only prefix is added.
        for letter in itertools.chain(string.ascii_lowercase, string.ascii_uppercase):
            try:
                eval(f'{letter}""')
                single_char_valid_prefixes.add(letter.lower())
            except SyntaxError:
                pass

        # This logic assumes that all combinations of valid prefixes only use
        # the characters that are valid single character prefixes.  That seems
        # like a valid assumption, but if it ever changes this will need
        # adjusting.
        valid_prefixes = set()
        for length in itertools.count():
            num_at_this_length = 0
            for prefix in (
                "".join(l)
                for l in itertools.combinations(single_char_valid_prefixes, length)
            ):
                for t in itertools.permutations(prefix):
                    for u in itertools.product(*[(c, c.upper()) for c in t]):
                        p = "".join(u)
                        if p == "not":
                            # 'not' can never be a string prefix,
                            # because it's a valid expression: not ""
                            continue
                        try:
                            eval(f'{p}""')

                            # No syntax error, so p is a valid string
                            # prefix.

                            valid_prefixes.add(p)
                            num_at_this_length += 1
                        except SyntaxError:
                            pass
            if num_at_this_length == 0:
                return valid_prefixes