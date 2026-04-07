def simple_block_tag(self, func=None, takes_context=None, name=None, end_name=None):
        """
        Register a callable as a compiled block template tag. Example:

        @register.simple_block_tag
        def hello(content):
            return 'world'
        """

        def dec(func):
            nonlocal end_name
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

            if end_name is None:
                end_name = f"end{function_name}"

            if takes_context:
                if len(params) >= 2 and params[1] == "content":
                    del params[1]
                else:
                    raise TemplateSyntaxError(
                        f"{function_name!r} is decorated with takes_context=True so"
                        " it must have a first argument of 'context' and a second "
                        "argument of 'content'"
                    )

                if params and params[0] == "context":
                    del params[0]
                else:
                    raise TemplateSyntaxError(
                        f"{function_name!r} is decorated with takes_context=True so it "
                        "must have a first argument of 'context'"
                    )
            elif params and params[0] == "content":
                del params[0]
            else:
                raise TemplateSyntaxError(
                    f"{function_name!r} must have a first argument of 'content'"
                )

            @wraps(func)
            def compile_func(parser, token):
                bits = token.split_contents()[1:]
                target_var = None
                if len(bits) >= 2 and bits[-2] == "as":
                    target_var = bits[-1]
                    bits = bits[:-2]

                nodelist = parser.parse((end_name,))
                parser.delete_first_token()

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

                return SimpleBlockNode(
                    nodelist, func, takes_context, args, kwargs, target_var
                )

            self.tag(function_name, compile_func)
            return func

        if func is None:
            # @register.simple_block_tag(...)
            return dec
        elif callable(func):
            # @register.simple_block_tag
            return dec(func)
        else:
            raise ValueError("Invalid arguments provided to simple_block_tag")