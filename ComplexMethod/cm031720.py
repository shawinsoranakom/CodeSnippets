def format_docstring_signature(
        f: Function, parameters: list[Parameter]
    ) -> str:
        lines = []
        lines.append(f.displayname)
        if f.forced_text_signature:
            lines.append(f.forced_text_signature)
        elif f.kind in {GETTER, SETTER}:
            # @getter and @setter do not need signatures like a method or a function.
            return ''
        else:
            lines.append('(')

            # populate "right_bracket_count" field for every parameter
            assert parameters, "We should always have a self parameter. " + repr(f)
            assert isinstance(parameters[0].converter, self_converter)
            # self is always positional-only.
            assert parameters[0].is_positional_only()
            assert parameters[0].right_bracket_count == 0
            positional_only = True
            for p in parameters[1:]:
                if not p.is_positional_only():
                    positional_only = False
                else:
                    assert positional_only
                if positional_only:
                    p.right_bracket_count = abs(p.group)
                else:
                    # don't put any right brackets around non-positional-only parameters, ever.
                    p.right_bracket_count = 0

            right_bracket_count = 0

            def fix_right_bracket_count(desired: int) -> str:
                nonlocal right_bracket_count
                s = ''
                while right_bracket_count < desired:
                    s += '['
                    right_bracket_count += 1
                while right_bracket_count > desired:
                    s += ']'
                    right_bracket_count -= 1
                return s

            need_slash = False
            added_slash = False
            need_a_trailing_slash = False

            # we only need a trailing slash:
            #   * if this is not a "docstring_only" signature
            #   * and if the last *shown* parameter is
            #     positional only
            if not f.docstring_only:
                for p in reversed(parameters):
                    if not p.converter.show_in_signature:
                        continue
                    if p.is_positional_only():
                        need_a_trailing_slash = True
                    break


            added_star = False

            first_parameter = True
            last_p = parameters[-1]
            line_length = len(''.join(lines))
            indent = " " * line_length
            def add_parameter(text: str) -> None:
                nonlocal line_length
                nonlocal first_parameter
                if first_parameter:
                    s = text
                    first_parameter = False
                else:
                    s = ' ' + text
                    if line_length + len(s) >= 72:
                        lines.extend(["\n", indent])
                        line_length = len(indent)
                        s = text
                line_length += len(s)
                lines.append(s)

            for p in parameters:
                if not p.converter.show_in_signature:
                    continue
                assert p.name

                is_self = isinstance(p.converter, self_converter)
                if is_self and f.docstring_only:
                    # this isn't a real machine-parsable signature,
                    # so let's not print the "self" parameter
                    continue

                if p.is_positional_only():
                    need_slash = not f.docstring_only
                elif need_slash and not (added_slash or p.is_positional_only()):
                    added_slash = True
                    add_parameter('/,')

                if p.is_keyword_only() and not added_star:
                    added_star = True
                    add_parameter('*,')

                p_lines = [fix_right_bracket_count(p.right_bracket_count)]

                if isinstance(p.converter, self_converter):
                    # annotate first parameter as being a "self".
                    #
                    # if inspect.Signature gets this function,
                    # and it's already bound, the self parameter
                    # will be stripped off.
                    #
                    # if it's not bound, it should be marked
                    # as positional-only.
                    #
                    # note: we don't print "self" for __init__,
                    # because this isn't actually the signature
                    # for __init__.  (it can't be, __init__ doesn't
                    # have a docstring.)  if this is an __init__
                    # (or __new__), then this signature is for
                    # calling the class to construct a new instance.
                    p_lines.append('$')

                if p.is_vararg():
                    p_lines.append("*")
                    added_star = True
                if p.is_var_keyword():
                    p_lines.append("**")

                name = p.converter.signature_name or p.name
                p_lines.append(name)

                if not p.is_variable_length() and p.converter.is_optional():
                    p_lines.append('=')
                    value = p.converter.py_default
                    if not value:
                        value = repr(p.converter.default)
                    p_lines.append(value)

                if (p != last_p) or need_a_trailing_slash:
                    p_lines.append(',')

                p_output = "".join(p_lines)
                add_parameter(p_output)

            lines.append(fix_right_bracket_count(0))
            if need_a_trailing_slash:
                add_parameter('/')
            lines.append(')')

        # PEP 8 says:
        #
        #     The Python standard library will not use function annotations
        #     as that would result in a premature commitment to a particular
        #     annotation style. Instead, the annotations are left for users
        #     to discover and experiment with useful annotation styles.
        #
        # therefore this is commented out:
        #
        # if f.return_converter.py_default:
        #     lines.append(' -> ')
        #     lines.append(f.return_converter.py_default)

        if not f.docstring_only:
            lines.append("\n" + libclinic.SIG_END_MARKER + "\n")

        signature_line = "".join(lines)

        # now fix up the places where the brackets look wrong
        return signature_line.replace(', ]', ',] ')