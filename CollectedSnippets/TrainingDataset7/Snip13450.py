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