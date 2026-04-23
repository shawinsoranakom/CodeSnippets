def display_name(self):
        res = TokenList(self)
        if len(res) == 0:
            return res.value
        if res[0].token_type == 'cfws':
            res.pop(0)
        else:
            if (isinstance(res[0], TokenList) and
                    res[0][0].token_type == 'cfws'):
                res[0] = TokenList(res[0][1:])
        if res[-1].token_type == 'cfws':
            res.pop()
        else:
            if (isinstance(res[-1], TokenList) and
                    res[-1][-1].token_type == 'cfws'):
                res[-1] = TokenList(res[-1][:-1])
        return res.value