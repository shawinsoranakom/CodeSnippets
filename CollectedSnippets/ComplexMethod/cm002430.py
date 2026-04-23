def _format_py_obj(obj, indent=0, mode="", cache=None, prefix=""):
    """Format python objects of basic built-in type in a pretty way so we could copy-past them to code editor easily.

    Currently, this support int, float, str, list, tuple, and dict.

    It also works with `torch.Tensor` via calling `format_tesnor`.
    """

    if cache is None:
        cache = {}
    else:
        if (id(obj), indent, mode, prefix) in cache:
            return cache[(id(obj), indent, mode, prefix)]

    # special format method for `torch.Tensor`
    if str(obj.__class__) == "<class 'torch.Tensor'>":
        return _format_tensor(obj)

    elif obj.__class__.__name__ == "str":
        quoted_string = _quote_string(obj)
        # we don't want the newline being interpreted
        quoted_string = quoted_string.replace("\n", r"\n")
        output = quoted_string

    elif obj.__class__.__name__ in ["int", "float"]:
        # for float like `1/3`, we will get `0.3333333333333333`
        output = str(obj)

    elif obj.__class__.__name__ in ["list", "tuple", "dict"]:
        parenthesis = {
            "list": "[]",
            "tuple": "()",
            "dict": "{}",
        }
        p1, p2 = parenthesis[obj.__class__.__name__]

        elements_without_indent = []
        if isinstance(obj, dict):
            for idx, (k, v) in enumerate(obj.items()):
                last_element = idx == len(obj) - 1
                ok = _format_py_obj(k, indent=indent + 1, mode="one-line", cache=cache)
                ov = _format_py_obj(
                    v,
                    indent=indent + 1,
                    mode=mode,
                    cache=cache,
                    prefix=ok.lstrip() + ": " + "," if not last_element else "",
                )
                # Each element could be multiple-line, but the indent of its first line is removed
                elements_without_indent.append(f"{ok.lstrip()}: {ov.lstrip()}")

        else:
            for idx, x in enumerate(obj):
                last_element = idx == len(obj) - 1
                o = _format_py_obj(
                    x, indent=indent + 1, mode=mode, cache=cache, prefix="," if not last_element else ""
                )
                # Each element could be multiple-line, but the indent of its first line is removed
                elements_without_indent.append(o.lstrip())

        groups = []
        buf = []
        for idx, x in enumerate(elements_without_indent):
            buf.append(x)

            x_expanded = "\n" in buf[-1]
            not_last_element = idx != len(elements_without_indent) - 1
            # if `x` should be separated from subsequent elements
            should_finalize_x = x_expanded or len(f"{' ' * (4 * (indent + 1))}") + len(
                ", ".join(buf[-1:])
            ) > 120 - int(not_last_element)

            # if `buf[:-1]` (i.e. without `x`) should be combined together (into one line)
            should_finalize_buf = x_expanded

            # the recursive call returns single line, so we can use it to determine if we can fit the width limit
            if not should_finalize_buf:
                buf_not_fit_into_one_line = len(f"{' ' * (4 * (indent + 1))}") + len(", ".join(buf)) > 120 - int(
                    not_last_element
                )
                should_finalize_buf = buf_not_fit_into_one_line

            # any element of iterable type need to be on its own line
            if (type(obj[idx]) if type(obj) is not dict else type(list(obj.values())[idx])) in [list, tuple, dict]:
                should_finalize_x = True
                should_finalize_buf = True

            # any type change --> need to be added after a new line
            prev_type = None
            current_type = type(obj[idx]) if type(obj) is not dict else type(list(obj.values())[idx])
            if len(buf) > 1:
                prev_type = type(obj[idx - 1]) if type(obj) is not dict else type(list(obj.values())[idx - 1])
                type_changed = current_type != prev_type
                if type_changed:
                    should_finalize_buf = True

            # all elements in the buf are string --> don't finalize the buf by width limit
            if prev_type is None or (prev_type is str and current_type is str):
                should_finalize_buf = False

            # collect as many elements of string type as possible (without width limit).
            # These will be examined as a whole (if not fit into the width, each element would be in its own line)
            if current_type is str:
                should_finalize_x = False
                # `len(buf) == 1` or `obj[idx-1]` is a string
                if prev_type in [None, str]:
                    should_finalize_buf = False

            if should_finalize_buf:
                orig_buf_len = len(buf)

                if orig_buf_len > 1:
                    not_fit_into_one_line = None

                    # all elements in `obj` that give `buf[:-1]` are string.
                    if prev_type is str:
                        # `-1` at the end: because buf[-2] is not the last element
                        not_fit_into_one_line = len(f"{' ' * (4 * (indent + 1))}") + len(", ".join(buf[:-1])) > 120 - 1

                    if not_fit_into_one_line:
                        for x in buf[:-1]:
                            groups.append([x])
                    else:
                        groups.append(buf[:-1])

                    buf = buf[-1:]

                if should_finalize_x:
                    groups.append(buf)
                    buf = []

        # The last buf
        if len(buf) > 0:
            not_fit_into_one_line = None
            if current_type is str:
                # no `-1` at the end: because buf[-1] is the last element
                not_fit_into_one_line = len(f"{' ' * (4 * (indent + 1))}") + len(", ".join(buf)) > 120

            if not_fit_into_one_line:
                for x in buf:
                    groups.append([x])
            else:
                groups.append(buf)

        output = f"{' ' * 4 * indent}{p1}\n"
        element_strings = [f"{' ' * (4 * (indent + 1))}" + ", ".join(buf) for buf in groups]
        output += ",\n".join(element_strings)
        output += f"\n{' ' * 4 * indent}{p2}"

        # if all elements are in one-line
        no_new_line_in_elements = all("\n" not in x for x in element_strings)
        # if yes, we can form a one-line representation of `obj`
        could_use_one_line = no_new_line_in_elements

        # if mode == "one-line", this function always returns one-line representation, so `no_new_line_in_elements`
        # will be `True`.
        if could_use_one_line:
            one_line_form = ", ".join([x.lstrip() for x in element_strings])
            one_line_form = f"{p1}{one_line_form}{p2}"

            if mode == "one-line":
                return output

            # check with the width limit
            could_use_one_line = len(f"{' ' * 4 * indent}") + len(prefix) + len(one_line_form) <= 120

            # extra conditions for returning one-line representation
            def use_one_line_repr(obj):
                # iterable types
                if type(obj) in (list, tuple, dict):
                    # get all types
                    element_types = []
                    if type(obj) is dict:
                        element_types.extend(type(x) for x in obj.values())
                    elif type(obj) in [list, tuple]:
                        element_types.extend(type(x) for x in obj)

                    # At least one element is of iterable type
                    if any(x in (list, tuple, dict) for x in element_types):
                        # If `obj` has more than one element and at least one of them is iterable --> no one line repr.
                        if len(obj) > 1:
                            return False

                        # only one element that is iterable, but not the same type as `obj` --> no one line repr.
                        if type(obj) is not type(obj[0]):
                            return False

                        # one-line repr. if possible, without width limit
                        return no_new_line_in_elements

                    # all elements are of simple types, but more than one type --> no one line repr.
                    if len(set(element_types)) > 1:
                        return False

                    # all elements are of the same simple type
                    if element_types[0] in [int, float]:
                        # one-line repr. without width limit
                        return no_new_line_in_elements
                    elif element_types[0] is str:
                        if len(obj) == 1:
                            # one single string element --> one-line repr. without width limit
                            return no_new_line_in_elements
                        else:
                            # multiple string elements --> one-line repr. if fit into width limit
                            return could_use_one_line

                # simple types (int, flat, string)
                return True

            # width condition combined with specific mode conditions
            if use_one_line_repr(obj):
                output = f"{' ' * 4 * indent}{one_line_form}"

    cache[(id(obj), indent, mode, prefix)] = output

    return output