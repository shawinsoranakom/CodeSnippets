def parse_import(self) -> Result:
        if self.code.rstrip().endswith('import') and self.code.endswith(' '):
            return Result(name='')
        if self.tokens.peek_string(','):
            name = ''
        else:
            if self.code.endswith(' '):
                raise ParseError('parse_import')
            name = self.parse_dotted_name()
        if name.startswith('.'):
            raise ParseError('parse_import')
        while self.tokens.peek_string(','):
            self.tokens.pop()
            self.parse_dotted_as_name()
        if self.tokens.peek_string('import'):
            return Result(name=name)
        raise ParseError('parse_import')