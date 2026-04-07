def parse_bits(
    parser,
    bits,
    params,
    varargs,
    varkw,
    defaults,
    kwonly,
    kwonly_defaults,
    name,
):
    """
    Parse bits for template tag helpers simple_tag and inclusion_tag, in
    particular by detecting syntax errors and by extracting positional and
    keyword arguments.
    """
    args = []
    kwargs = {}
    unhandled_params = list(params)
    unhandled_kwargs = [
        kwarg for kwarg in kwonly if not kwonly_defaults or kwarg not in kwonly_defaults
    ]
    for bit in bits:
        # First we try to extract a potential kwarg from the bit
        kwarg = token_kwargs([bit], parser)
        if kwarg:
            # The kwarg was successfully extracted
            param, value = kwarg.popitem()
            if param not in params and param not in kwonly and varkw is None:
                # An unexpected keyword argument was supplied
                raise TemplateSyntaxError(
                    "'%s' received unexpected keyword argument '%s'" % (name, param)
                )
            elif param in kwargs:
                # The keyword argument has already been supplied once
                raise TemplateSyntaxError(
                    "'%s' received multiple values for keyword argument '%s'"
                    % (name, param)
                )
            else:
                # All good, record the keyword argument
                kwargs[str(param)] = value
                if param in unhandled_params:
                    # If using the keyword syntax for a positional arg, then
                    # consume it.
                    unhandled_params.remove(param)
                elif param in unhandled_kwargs:
                    # Same for keyword-only arguments
                    unhandled_kwargs.remove(param)
        else:
            if kwargs:
                raise TemplateSyntaxError(
                    "'%s' received some positional argument(s) after some "
                    "keyword argument(s)" % name
                )
            else:
                # Record the positional argument
                args.append(parser.compile_filter(bit))
                try:
                    # Consume from the list of expected positional arguments
                    unhandled_params.pop(0)
                except IndexError:
                    if varargs is None:
                        raise TemplateSyntaxError(
                            "'%s' received too many positional arguments" % name
                        )
    if defaults is not None:
        # Consider the last n params handled, where n is the
        # number of defaults.
        unhandled_params = unhandled_params[: -len(defaults)]
    if unhandled_params or unhandled_kwargs:
        # Some positional arguments were not supplied
        raise TemplateSyntaxError(
            "'%s' did not receive value(s) for the argument(s): %s"
            % (name, ", ".join("'%s'" % p for p in unhandled_params + unhandled_kwargs))
        )
    return args, kwargs