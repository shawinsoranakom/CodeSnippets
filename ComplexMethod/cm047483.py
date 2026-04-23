def filter_function(self, records: M, field_expr: str, operator: str, value) -> Callable[[M], M]:
        assert operator not in Domain.NEGATIVE_OPERATORS, "only positive operators are implemented"
        getter = self.expression_getter(field_expr)
        # assert not isinstance(value, (SQL, Query))

        # -------------------------------------------------
        # operator: in (equality)
        if operator == 'in':
            assert isinstance(value, COLLECTION_TYPES) and value, \
                f"filter_function() 'in' operator expects a collection, not a {type(value)}"
            if not isinstance(value, AbstractSet):
                value = set(value)
            if False in value or self.falsy_value in value:
                if len(value) == 1:
                    return lambda rec: not getter(rec)
                return lambda rec: (val := getter(rec)) in value or not val
            return lambda rec: getter(rec) in value

        # -------------------------------------------------
        # operator: like
        if operator.endswith('like'):
            # we may get a value which is not a string
            if operator.endswith('ilike'):
                # ilike uses unaccent and lower-case comparison
                unaccent_python = records.env.registry.unaccent_python

                def unaccent(x):
                    return unaccent_python(str(x).lower()) if x else ''
            else:
                def unaccent(x):
                    return str(x) if x else ''

            # build a regex that matches the SQL-like expression
            # note that '\' is used for escaping in SQL
            def build_like_regex(value: str, exact: bool):
                yield '^' if exact else '.*'
                escaped = False
                for char in value:
                    if escaped:
                        escaped = False
                        yield re.escape(char)
                    elif char == '\\':
                        escaped = True
                    elif char == '%':
                        yield '.*'
                    elif char == '_':
                        yield '.'
                    else:
                        yield re.escape(char)
                if exact:
                    yield '$'
                # no need to match r'.*' in else because we only use .match()

            like_regex = re.compile("".join(build_like_regex(unaccent(value), "=" in operator)), flags=re.DOTALL)
            return lambda rec: like_regex.match(unaccent(getter(rec)))

        # -------------------------------------------------
        # operator: inequality
        if pyop := PYTHON_INEQUALITY_OPERATOR.get(operator):
            can_be_null = False
            if (null_value := self.falsy_value) is not None:
                value = value or null_value
                can_be_null = (
                    null_value < value if operator == '<' else
                    null_value > value if operator == '>' else
                    null_value <= value if operator == '<=' else
                    null_value >= value  # operator == '>='
                )

            def check_inequality(rec):
                rec_value = getter(rec)
                try:
                    if rec_value is False or rec_value is None:
                        return can_be_null
                    return pyop(rec_value, value)
                except (ValueError, TypeError):
                    # ignoring error, type mismatch
                    return False
            return check_inequality

        # -------------------------------------------------
        raise NotImplementedError(f"Invalid simple operator {operator!r}")