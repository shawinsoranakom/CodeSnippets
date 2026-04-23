def __init__(self, name, parser, token, func, template_name, takes_context=True):
        self.template_name = template_name
        with lazy_annotations():
            params, varargs, varkw, defaults, kwonly, kwonly_defaults, _ = (
                getfullargspec(func)
            )
        if takes_context:
            if params and params[0] == "context":
                del params[0]
            else:
                function_name = func.__name__
                raise TemplateSyntaxError(
                    f"{name!r} sets takes_context=True so {function_name!r} "
                    "must have a first argument of 'context'"
                )
        bits = token.split_contents()
        args, kwargs = parse_bits(
            parser,
            bits[1:],
            params,
            varargs,
            varkw,
            defaults,
            kwonly,
            kwonly_defaults,
            bits[0],
        )
        super().__init__(func, takes_context, args, kwargs, filename=None)