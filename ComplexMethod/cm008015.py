def _build_format_filter(self, filter_spec):
        " Returns a function to filter the formats according to the filter_spec "

        OPERATORS = {
            '<': operator.lt,
            '<=': operator.le,
            '>': operator.gt,
            '>=': operator.ge,
            '=': operator.eq,
            '!=': operator.ne,
        }
        operator_rex = re.compile(r'''(?x)\s*
            (?P<key>[\w.-]+)\s*
            (?P<op>{})(?P<none_inclusive>\s*\?)?\s*
            (?P<value>[0-9.]+(?:[kKmMgGtTpPeEzZyY]i?[Bb]?)?)\s*
            '''.format('|'.join(map(re.escape, OPERATORS.keys()))))
        m = operator_rex.fullmatch(filter_spec)
        if m:
            try:
                comparison_value = float(m.group('value'))
            except ValueError:
                comparison_value = parse_filesize(m.group('value'))
                if comparison_value is None:
                    comparison_value = parse_filesize(m.group('value') + 'B')
                if comparison_value is None:
                    raise ValueError(
                        'Invalid value {!r} in format specification {!r}'.format(
                            m.group('value'), filter_spec))
            op = OPERATORS[m.group('op')]

        if not m:
            STR_OPERATORS = {
                '=': operator.eq,
                '^=': lambda attr, value: attr.startswith(value),
                '$=': lambda attr, value: attr.endswith(value),
                '*=': lambda attr, value: value in attr,
                '~=': lambda attr, value: value.search(attr) is not None,
            }
            str_operator_rex = re.compile(r'''(?x)\s*
                (?P<key>[a-zA-Z0-9._-]+)\s*
                (?P<negation>!\s*)?(?P<op>{})\s*(?P<none_inclusive>\?\s*)?
                (?P<quote>["'])?
                (?P<value>(?(quote)(?:(?!(?P=quote))[^\\]|\\.)+|[\w.-]+))
                (?(quote)(?P=quote))\s*
                '''.format('|'.join(map(re.escape, STR_OPERATORS.keys()))))
            m = str_operator_rex.fullmatch(filter_spec)
            if m:
                if m.group('op') == '~=':
                    comparison_value = re.compile(m.group('value'))
                else:
                    comparison_value = re.sub(r'''\\([\\"'])''', r'\1', m.group('value'))
                str_op = STR_OPERATORS[m.group('op')]
                if m.group('negation'):
                    op = lambda attr, value: not str_op(attr, value)
                else:
                    op = str_op

        if not m:
            raise SyntaxError(f'Invalid filter specification {filter_spec!r}')

        def _filter(f):
            actual_value = f.get(m.group('key'))
            if actual_value is None:
                return m.group('none_inclusive')
            return op(actual_value, comparison_value)
        return _filter