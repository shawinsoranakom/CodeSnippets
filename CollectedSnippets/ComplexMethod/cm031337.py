def parse_dotted_name(self) -> str:
        name = []
        if self.tokens.peek_string('.'):
            name.append('.')
            self.tokens.pop()
        if (self.tokens.peek_name()
            and (tok := self.tokens.peek())
            and tok.string not in self._keywords):
            name.append(self.tokens.pop_name())
        if not name:
            raise ParseError('parse_dotted_name')
        while self.tokens.peek_string('.'):
            name.append('.')
            self.tokens.pop()
            if (self.tokens.peek_name()
                and (tok := self.tokens.peek())
                and tok.string not in self._keywords):
                name.append(self.tokens.pop_name())
            else:
                break

        while self.tokens.peek_string('.'):
            name.append('.')
            self.tokens.pop()
        return ''.join(name[::-1])