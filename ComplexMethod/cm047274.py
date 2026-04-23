def _compile_expr_tokens(self, tokens, allowed_keys, argument_names=None, raise_on_missing=False):
        """ Transform the list of token coming into a python instruction in
            textual form by adding the namepaces for the dynamic values.

            Example: `5 + a + b.c` to be `5 + values.get('a') + values['b'].c`
            Unknown values are considered to be None, but using `values['b']`
            gives a clear error message in cases where there is an attribute for
            example (have a `KeyError: 'b'`, instead of `AttributeError: 'NoneType'
            object has no attribute 'c'`).

            @returns str
        """
        # Finds and extracts the current "scope"'s "allowed values": values
        # which should not be accessed through the environment's namespace:
        # * the local variables of a lambda should be accessed directly e.g.
        #     lambda a: a + b should be compiled to lambda a: a + values['b'],
        #     since a is local to the lambda it has to be accessed directly
        #     but b needs to be accessed through the rendering environment
        # * similarly for a comprehensions [a + b for a in c] should be
        #     compiledto [a + values.get('b') for a in values.get('c')]
        # to avoid the risk of confusion between nested lambdas / comprehensions,
        # this is currently performed independently at each level of brackets
        # nesting (hence the function being recursive).
        open_bracket_index = -1
        bracket_depth = 0

        argument_name = '_arg_%s__'
        argument_names = argument_names or []

        for index, t in enumerate(tokens):
            if t.exact_type in [token.LPAR, token.LSQB, token.LBRACE]:
                bracket_depth += 1
            elif t.exact_type in [token.RPAR, token.RSQB, token.RBRACE]:
                bracket_depth -= 1
            elif bracket_depth == 0 and t.exact_type == token.NAME:
                string = t.string
                if string == 'lambda': # lambda => allowed values for the current bracket depth
                    for i in range(index + 1, len(tokens)):
                        t = tokens[i]
                        if t.exact_type == token.NAME:
                            argument_names.append(t.string)
                        elif t.exact_type == token.COMMA:
                            pass
                        elif t.exact_type == token.COLON:
                            break
                        elif t.exact_type == token.EQUAL:
                            raise NotImplementedError('Lambda default values are not supported')
                        else:
                            raise NotImplementedError('This lambda code style is not implemented.')
                elif string == 'for': # list comprehensions => allowed values for the current bracket depth
                    for i in range(index + 1, len(tokens)):
                        t = tokens[i]
                        if t.exact_type == token.NAME:
                            if t.string == 'in':
                                break
                            argument_names.append(t.string)
                        elif t.exact_type in [token.COMMA, token.LPAR, token.RPAR]:
                            pass
                        else:
                            raise NotImplementedError('This loop code style is not implemented.')

        # Use bracket to nest structures.
        # Recursively processes the "sub-scopes", and replace their content with
        # a compiled node. During this recursive call we add to the allowed
        # values the values provided by the list comprehension, lambda, etc.,
        # previously extracted.
        index = 0
        open_bracket_index = -1
        bracket_depth = 0

        while index < len(tokens):
            t = tokens[index]
            string = t.string

            if t.exact_type in [token.LPAR, token.LSQB, token.LBRACE]:
                if bracket_depth == 0:
                    open_bracket_index = index
                bracket_depth += 1
            elif t.exact_type in [token.RPAR, token.RSQB, token.RBRACE]:
                bracket_depth -= 1
                if bracket_depth == 0:
                    code = self._compile_expr_tokens(
                        tokens[open_bracket_index + 1:index],
                        list(allowed_keys),
                        list(argument_names),
                        raise_on_missing,
                    )
                    code = tokens[open_bracket_index].string + code + t.string
                    tokens[open_bracket_index:index + 1] = [tokenize.TokenInfo(token.QWEB, code, tokens[open_bracket_index].start, t.end, '')]
                    index = open_bracket_index

            index += 1

        # The keys will be namespaced by values if they are not allowed. In
        # order to have a clear keyError message, this will be replaced by
        # values['key'] for certain cases (for example if an attribute is called
        # key.attrib, or an index key[0] ...)
        code = []
        index = 0
        pos = tokens and tokens[0].start # to keep level when use expr on multi line
        while index < len(tokens):
            t = tokens[index]
            string = t.string

            if t.start[0] != pos[0]:
                pos = (t.start[0], 0)
            space = t.start[1] - pos[1]
            if space:
                code.append(' ' * space)
            pos = t.start

            if t.exact_type == token.NAME:
                if '__' in string:
                    raise SyntaxError(f"Using variable names with '__' is not allowed: {string!r}")
                if string == 'lambda': # lambda => allowed values
                    code.append('lambda ')
                    index += 1
                    while index < len(tokens):
                        t = tokens[index]
                        if t.exact_type == token.NAME and t.string in argument_names:
                            code.append(argument_name % t.string)
                        if t.exact_type in [token.COMMA, token.COLON]:
                            code.append(t.string)
                        if t.exact_type == token.COLON:
                            break
                        index += 1
                    if t.end[0] != pos[0]:
                        pos = (t.end[0], 0)
                    else:
                        pos = t.end
                elif string in argument_names:
                    code.append(argument_name % t.string)
                elif string in allowed_keys:
                    code.append(string)
                elif index + 1 < len(tokens) and tokens[index + 1].exact_type == token.EQUAL: # function kw
                    code.append(string)
                elif index > 0 and tokens[index - 1] and tokens[index - 1].exact_type == token.DOT:
                    code.append(string)
                elif raise_on_missing or index + 1 < len(tokens) and tokens[index + 1].exact_type in [token.DOT, token.LPAR, token.LSQB, token.QWEB]:
                    # Should have values['product'].price to raise an error when get
                    # the 'product' value and not an 'NoneType' object has no
                    # attribute 'price' error.
                    code.append(f'values[{string!r}]')
                else:
                    # not assignation allowed, only getter
                    code.append(f'values.get({string!r})')
            elif t.type not in [tokenize.ENCODING, token.ENDMARKER, token.DEDENT]:
                code.append(string)

            if t.end[0] != pos[0]:
                pos = (t.end[0], 0)
            else:
                pos = t.end

            index += 1

        return ''.join(code)