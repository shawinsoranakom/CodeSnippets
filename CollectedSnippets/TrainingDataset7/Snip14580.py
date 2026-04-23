def normalize(pattern):
    r"""
    Given a reg-exp pattern, normalize it to an iterable of forms that
    suffice for reverse matching. This does the following:

    (1) For any repeating sections, keeps the minimum number of occurrences
        permitted (this means zero for optional groups).
    (2) If an optional group includes parameters, include one occurrence of
        that group (along with the zero occurrence case from step (1)).
    (3) Select the first (essentially an arbitrary) element from any character
        class. Select an arbitrary character for any unordered class (e.g. '.'
        or '\w') in the pattern.
    (4) Ignore look-ahead and look-behind assertions.
    (5) Raise an error on any disjunctive ('|') constructs.

    Django's URLs for forward resolving are either all positional arguments or
    all keyword arguments. That is assumed here, as well. Although reverse
    resolving can be done using positional args when keyword args are
    specified, the two cannot be mixed in the same reverse() call.
    """
    # Do a linear scan to work out the special features of this pattern. The
    # idea is that we scan once here and collect all the information we need to
    # make future decisions.
    result = []
    non_capturing_groups = []
    consume_next = True
    pattern_iter = next_char(iter(pattern))
    num_args = 0

    # A "while" loop is used here because later on we need to be able to peek
    # at the next character and possibly go around without consuming another
    # one at the top of the loop.
    try:
        ch, escaped = next(pattern_iter)
    except StopIteration:
        return [("", [])]

    try:
        while True:
            if escaped:
                result.append(ch)
            elif ch == ".":
                # Replace "any character" with an arbitrary representative.
                result.append(".")
            elif ch == "|":
                # FIXME: One day we'll should do this, but not in 1.0.
                raise NotImplementedError("Awaiting Implementation")
            elif ch == "^":
                pass
            elif ch == "$":
                break
            elif ch == ")":
                # This can only be the end of a non-capturing group, since all
                # other unescaped parentheses are handled by the grouping
                # section later (and the full group is handled there).
                #
                # We regroup everything inside the capturing group so that it
                # can be quantified, if necessary.
                start = non_capturing_groups.pop()
                inner = NonCapture(result[start:])
                result = result[:start] + [inner]
            elif ch == "[":
                # Replace ranges with the first character in the range.
                ch, escaped = next(pattern_iter)
                result.append(ch)
                ch, escaped = next(pattern_iter)
                while escaped or ch != "]":
                    ch, escaped = next(pattern_iter)
            elif ch == "(":
                # Some kind of group.
                ch, escaped = next(pattern_iter)
                if ch != "?" or escaped:
                    # A positional group
                    name = "_%d" % num_args
                    num_args += 1
                    result.append(Group((("%%(%s)s" % name), name)))
                    walk_to_end(ch, pattern_iter)
                else:
                    ch, escaped = next(pattern_iter)
                    if ch in "!=<":
                        # All of these are ignorable. Walk to the end of the
                        # group.
                        walk_to_end(ch, pattern_iter)
                    elif ch == ":":
                        # Non-capturing group
                        non_capturing_groups.append(len(result))
                    elif ch != "P":
                        # Anything else, other than a named group, is something
                        # we cannot reverse.
                        raise ValueError("Non-reversible reg-exp portion: '(?%s'" % ch)
                    else:
                        ch, escaped = next(pattern_iter)
                        if ch not in ("<", "="):
                            raise ValueError(
                                "Non-reversible reg-exp portion: '(?P%s'" % ch
                            )
                        # We are in a named capturing group. Extra the name and
                        # then skip to the end.
                        if ch == "<":
                            terminal_char = ">"
                        # We are in a named backreference.
                        else:
                            terminal_char = ")"
                        name = []
                        ch, escaped = next(pattern_iter)
                        while ch != terminal_char:
                            name.append(ch)
                            ch, escaped = next(pattern_iter)
                        param = "".join(name)
                        # Named backreferences have already consumed the
                        # parenthesis.
                        if terminal_char != ")":
                            result.append(Group((("%%(%s)s" % param), param)))
                            walk_to_end(ch, pattern_iter)
                        else:
                            result.append(Group((("%%(%s)s" % param), None)))
            elif ch in "*?+{":
                # Quantifiers affect the previous item in the result list.
                count, ch = get_quantifier(ch, pattern_iter)
                if ch:
                    # We had to look ahead, but it wasn't need to compute the
                    # quantifier, so use this character next time around the
                    # main loop.
                    consume_next = False

                if count == 0:
                    if contains(result[-1], Group):
                        # If we are quantifying a capturing group (or
                        # something containing such a group) and the minimum is
                        # zero, we must also handle the case of one occurrence
                        # being present. All the quantifiers (except {0,0},
                        # which we conveniently ignore) that have a 0 minimum
                        # also allow a single occurrence.
                        result[-1] = Choice([None, result[-1]])
                    else:
                        result.pop()
                elif count > 1:
                    result.extend([result[-1]] * (count - 1))
            else:
                # Anything else is a literal.
                result.append(ch)

            if consume_next:
                ch, escaped = next(pattern_iter)
            consume_next = True
    except StopIteration:
        pass
    except NotImplementedError:
        # A case of using the disjunctive form. No results for you!
        return [("", [])]

    return list(zip(*flatten_result(result)))