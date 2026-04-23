def inclusion_tag(self, filename, func=None, takes_context=None, name=None):
        """
        Register a callable as an inclusion tag:

        @register.inclusion_tag('results.html')
        def show_results(poll):
            choices = poll.choice_set.all()
            return {'choices': choices}
        """

        def dec(func):
            with lazy_annotations():
                (
                    params,
                    varargs,
                    varkw,
                    defaults,
                    kwonly,
                    kwonly_defaults,
                    _,
                ) = getfullargspec(unwrap(func))
            function_name = name or func.__name__

            if takes_context:
                if params and params[0] == "context":
                    params = params[1:]
                else:
                    raise TemplateSyntaxError(
                        f"{function_name!r} is decorated with takes_context=True so it "
                        "must have a first argument of 'context'"
                    )

            @wraps(func)
            def compile_func(parser, token):
                bits = token.split_contents()[1:]
                args, kwargs = parse_bits(
                    parser,
                    bits,
                    params,
                    varargs,
                    varkw,
                    defaults,
                    kwonly,
                    kwonly_defaults,
                    function_name,
                )
                return InclusionNode(
                    func,
                    takes_context,
                    args,
                    kwargs,
                    filename,
                )

            self.tag(function_name, compile_func)
            return func

        return dec