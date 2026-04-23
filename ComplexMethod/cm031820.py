def members(self, allow_sequence : bool=False) -> list[str] | None:
        here = self.getpos()
        if tkn := self.expect(lx.IDENTIFIER):
            members = [tkn.text]
            while self.expect(lx.COMMA):
                if tkn := self.expect(lx.IDENTIFIER):
                    members.append(tkn.text)
                else:
                    break
            peek = self.peek()
            kinds = [lx.RBRACE, lx.RBRACKET] if allow_sequence else [lx.RBRACE]
            if not peek or peek.kind not in kinds:
                raise self.make_syntax_error(
                    f"Expected comma or right paren{'/bracket' if allow_sequence else ''}")
            return members
        self.setpos(here)
        return None