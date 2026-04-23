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