def create_template_error(ex: Exception, variable: t.Any, is_expression: bool) -> AnsibleTemplateError:
    if isinstance(ex, AnsibleTemplateError):
        exception_to_raise = ex
    else:
        kind = "expression" if is_expression else "template"
        ex_type = AnsibleTemplateError  # always raise an AnsibleTemplateError/subclass

        if isinstance(ex, RecursionError):
            msg = f"Recursive loop detected in {kind}."
        elif isinstance(ex, TemplateSyntaxError):
            if (origin := Origin.get_tag(variable)) and origin.line_num is None and ex.lineno > 0:
                # When there is an origin without a line number, use the line number provided by the Jinja syntax error.
                # This should only occur on templates which represent the entire contents of a file.
                # Templates loaded from within a file, such as YAML, will use the existing origin.
                # It's not possible to combine origins here, due to potential layout differences between the original content and the parsed output.
                # This can happen, for example, with YAML multi-line strings.
                variable = origin.replace(line_num=ex.lineno, col_num=None).tag(variable)

            msg = f"Syntax error in {kind}."

            if is_expression and is_possibly_template(variable):
                msg += " Template delimiters are not supported in expressions."

            ex_type = AnsibleTemplateSyntaxError
        else:
            msg = f"Error rendering {kind}."

        exception_to_raise = ex_type(msg, obj=variable)

    if exception_to_raise.obj is None:
        exception_to_raise.obj = TemplateContext.current().template_value

    # DTFIX-FUTURE: Look through the TemplateContext hierarchy to find the most recent non-template
    #   caller and use that for origin when no origin is available on obj. This could be useful for situations where the template
    #   was embedded in a plugin, or a plugin is otherwise responsible for losing the origin and/or trust. We can't just use the first
    #   non-template caller as that will lead to false positives for re-entrant calls (e.g. template plugins that call into templar).

    return exception_to_raise