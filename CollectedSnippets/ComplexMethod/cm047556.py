def _read_group_having(self, having_domain: list, query: Query) -> SQL:
        """ Return <SQL expression> corresponding to the having domain.
        """
        if not having_domain:
            return SQL()

        stack: list[SQL] = []
        SUPPORTED = ('in', 'not in', '<', '>', '<=', '>=', '=', '!=')
        for item in reversed(having_domain):
            if item == '!':
                stack.append(SQL("(NOT %s)", stack.pop()))
            elif item == '&':
                stack.append(SQL("(%s AND %s)", stack.pop(), stack.pop()))
            elif item == '|':
                stack.append(SQL("(%s OR %s)", stack.pop(), stack.pop()))
            elif isinstance(item, (list, tuple)) and len(item) == 3:
                left, operator, right = item
                if operator not in SUPPORTED:
                    raise ValueError(f"Invalid having clause {item!r}: supported comparators are {SUPPORTED}")
                sql_left = self._read_group_select(left, query)
                stack.append(SQL("%s%s%s", sql_left, SQL_OPERATORS[operator], right))
            else:
                raise ValueError(f"Invalid having clause {item!r}: it should be a domain-like clause")

        while len(stack) > 1:
            stack.append(SQL("(%s AND %s)", stack.pop(), stack.pop()))

        return stack[0]