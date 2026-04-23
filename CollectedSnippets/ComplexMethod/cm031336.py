def parse_from_import(self) -> Result:
        stripped = self.code.rstrip()
        if stripped.endswith('import') and self.code.endswith(' '):
            return Result(from_name=self.parse_empty_from_import(), name='')
        if stripped.endswith('from') and self.code.endswith(' '):
            return Result(from_name='')
        if self.tokens.peek_string('(') or self.tokens.peek_string(','):
            return Result(from_name=self.parse_empty_from_import(), name='')
        if self.code.endswith(' '):
            raise ParseError('parse_from_import')
        name = self.parse_dotted_name()
        if '.' in name:
            self.tokens.pop_string('from')
            return Result(from_name=name)
        if self.tokens.peek_string('from'):
            return Result(from_name=name)
        from_name = self.parse_empty_from_import()
        return Result(from_name=from_name, name=name)