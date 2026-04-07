def _parse_table_constraints(self, sql, columns):
        # Check constraint parsing is based of SQLite syntax diagram.
        # https://www.sqlite.org/syntaxdiagrams.html#table-constraint
        statement = sqlparse.parse(sql)[0]
        constraints = {}
        unnamed_constrains_index = 0
        tokens = (token for token in statement.flatten() if not token.is_whitespace)
        # Go to columns and constraint definition
        for token in tokens:
            if token.match(sqlparse.tokens.Punctuation, "("):
                break
        # Parse columns and constraint definition
        while True:
            (
                constraint_name,
                unique,
                check,
                end_token,
            ) = self._parse_column_or_constraint_definition(tokens, columns)
            if unique:
                if constraint_name:
                    constraints[constraint_name] = unique
                else:
                    unnamed_constrains_index += 1
                    constraints[
                        "__unnamed_constraint_%s__" % unnamed_constrains_index
                    ] = unique
            if check:
                if constraint_name:
                    constraints[constraint_name] = check
                else:
                    unnamed_constrains_index += 1
                    constraints[
                        "__unnamed_constraint_%s__" % unnamed_constrains_index
                    ] = check
            if end_token.match(sqlparse.tokens.Punctuation, ")"):
                break
        return constraints