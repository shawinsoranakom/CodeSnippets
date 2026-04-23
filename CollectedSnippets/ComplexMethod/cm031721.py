def format_docstring(self) -> str:
        assert self.function is not None
        f = self.function
        # For the following special cases, it does not make sense to render a docstring.
        if f.kind in {METHOD_INIT, METHOD_NEW, GETTER, SETTER} and not f.docstring:
            return f.docstring

        # Enforce the summary line!
        # The first line of a docstring should be a summary of the function.
        # It should fit on one line (80 columns? 79 maybe?) and be a paragraph
        # by itself.
        #
        # Argument Clinic enforces the following rule:
        #  * either the docstring is empty,
        #  * or it must have a summary line.
        #
        # Guido said Clinic should enforce this:
        # http://mail.python.org/pipermail/python-dev/2013-June/127110.html

        lines = f.docstring.split('\n')
        if len(lines) >= 2:
            if lines[1]:
                fail(f"Docstring for {f.full_name!r} does not have a summary line!\n"
                     "Every non-blank function docstring must start with "
                     "a single line summary followed by an empty line.")
        elif len(lines) == 1:
            # the docstring is only one line right now--the summary line.
            # add an empty line after the summary line so we have space
            # between it and the {parameters} we're about to add.
            lines.append('')

        # Fail if the summary line is too long.
        # Warn if any of the body lines are too long.
        # Existing violations are recorded in OVERLONG_{SUMMARY,BODY}.
        max_width = f.docstring_line_width
        summary_len = len(lines[0])
        max_body = max(map(len, lines[1:]))
        if summary_len > max_width:
            if not self.permit_long_summary:
                fail(f"Summary line for {f.full_name!r} is too long!\n"
                     f"The summary line must be no longer than {max_width} characters.")
        else:
            if self.permit_long_summary:
                warn("Remove the @permit_long_summary decorator from "
                     f"{f.full_name!r}!\n")

        if max_body > max_width:
            if not self.permit_long_docstring_body:
                warn(f"Docstring lines for {f.full_name!r} are too long!\n"
                     f"Lines should be no longer than {max_width} characters.")
        else:
            if self.permit_long_docstring_body:
                warn("Remove the @permit_long_docstring_body decorator from "
                     f"{f.full_name!r}!\n")

        parameters_marker_count = len(f.docstring.split('{parameters}')) - 1
        if parameters_marker_count > 1:
            fail('You may not specify {parameters} more than once in a docstring!')

        # insert signature at front and params after the summary line
        if not parameters_marker_count:
            lines.insert(2, '{parameters}')
        lines.insert(0, '{signature}')

        # finalize docstring
        params = f.render_parameters
        parameters = self.format_docstring_parameters(params)
        signature = self.format_docstring_signature(f, params)
        docstring = "\n".join(lines)
        return libclinic.linear_format(docstring,
                                       signature=signature,
                                       parameters=parameters).rstrip()