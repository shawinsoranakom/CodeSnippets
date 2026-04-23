def local_part(self):
        # Strip whitespace from front, back, and around dots.
        res = [DOT]
        last = DOT
        last_is_tl = False
        for tok in self[0] + [DOT]:
            if tok.token_type == 'cfws':
                continue
            if (last_is_tl and tok.token_type == 'dot' and
                    last[-1].token_type == 'cfws'):
                res[-1] = TokenList(last[:-1])
            is_tl = isinstance(tok, TokenList)
            if (is_tl and last.token_type == 'dot' and
                    tok[0].token_type == 'cfws'):
                res.append(TokenList(tok[1:]))
            else:
                res.append(tok)
            last = res[-1]
            last_is_tl = is_tl
        res = TokenList(res[1:-1])
        return res.value