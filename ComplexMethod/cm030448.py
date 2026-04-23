def value(self):
        quote = False
        if self.defects:
            quote = True
        else:
            for x in self:
                if x.token_type == 'quoted-string':
                    quote = True
        if len(self) != 0 and quote:
            pre = post = ''
            if (self[0].token_type == 'cfws' or
                isinstance(self[0], TokenList) and
                self[0][0].token_type == 'cfws'):
                pre = ' '
            if (self[-1].token_type == 'cfws' or
                isinstance(self[-1], TokenList) and
                self[-1][-1].token_type == 'cfws'):
                post = ' '
            return pre+quote_string(self.display_name)+post
        else:
            return super().value