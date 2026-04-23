def _search_full_name(self, operator, operand):
        if operator in Domain.NEGATIVE_OPERATORS:
            return NotImplemented

        if isinstance(operand, str):
            def make_operand(val): return val
            operands = [operand]
        else:
            def make_operand(val): return [val]
            operands = operand

        where_domains = [Domain('name', operator, operand)]
        for group in operands:
            if not group:
                continue
            domain = Domain('name', operator, make_operand(group))
            where_domains.append(domain)

            if '/' in group:
                privilege_name, _, group_name = group.partition('/')
                group_name = group_name.strip()
                privilege_name = privilege_name.strip()
            else:
                privilege_name = group
                group_name = None

            if privilege_name:
                domain = Domain(
                    'privilege_id', 'any!', Domain('name', operator, make_operand(privilege_name)),
                )
                if group_name:
                    domain &= Domain('name', operator, make_operand(group_name))
                where_domains.append(domain)

        return Domain.OR(where_domains)