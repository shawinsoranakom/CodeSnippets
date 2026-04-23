def pseudo_def(self) -> Pseudo | None:
        if (tkn := self.expect(lx.IDENTIFIER)) and tkn.text == "pseudo":
            size = None
            if self.expect(lx.LPAREN):
                if tkn := self.expect(lx.IDENTIFIER):
                    if self.expect(lx.COMMA):
                        inp, outp = self.io_effect()
                        if self.expect(lx.COMMA):
                            flags = self.flags()
                        else:
                            flags = []
                        if self.expect(lx.RPAREN):
                            if self.expect(lx.EQUALS):
                                if self.expect(lx.LBRACE):
                                    as_sequence = False
                                    closing = lx.RBRACE
                                elif self.expect(lx.LBRACKET):
                                    as_sequence = True
                                    closing = lx.RBRACKET
                                else:
                                    raise self.make_syntax_error("Expected { or [")
                                if members := self.members(allow_sequence=True):
                                    if self.expect(closing) and self.expect(lx.SEMI):
                                        return Pseudo(
                                            tkn.text, inp, outp, flags, members, as_sequence
                                        )
        return None