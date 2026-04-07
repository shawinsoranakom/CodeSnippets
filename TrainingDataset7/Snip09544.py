def _parse_constraint_columns(self, check_clause, columns):
        check_columns = OrderedSet()
        statement = sqlparse.parse(check_clause)[0]
        tokens = (token for token in statement.flatten() if not token.is_whitespace)
        for token in tokens:
            if (
                token.ttype == sqlparse.tokens.Name
                and self.connection.ops.quote_name(token.value) == token.value
                and token.value[1:-1] in columns
            ):
                check_columns.add(token.value[1:-1])
        return check_columns