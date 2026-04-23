def _replace_convenience_variables(self, line):
        """Replace the convenience variables in 'line' with their values.
           e.g. $foo is replaced by __pdb_convenience_variables["foo"].
           Note: such pattern in string literals will be skipped"""

        if "$" not in line:
            return line

        dollar_start = dollar_end = (-1, -1)
        replace_variables = []
        try:
            for t in tokenize.generate_tokens(io.StringIO(line).readline):
                token_type, token_string, start, end, _ = t
                if token_type == token.OP and token_string == '$':
                    dollar_start, dollar_end = start, end
                elif start == dollar_end and token_type == token.NAME:
                    # line is a one-line command so we only care about column
                    replace_variables.append((dollar_start[1], end[1], token_string))
        except tokenize.TokenError:
            return line

        if not replace_variables:
            return line

        last_end = 0
        line_pieces = []
        for start, end, name in replace_variables:
            line_pieces.append(line[last_end:start] + f'__pdb_convenience_variables["{name}"]')
            last_end = end
        line_pieces.append(line[last_end:])

        return ''.join(line_pieces)