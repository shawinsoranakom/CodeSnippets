def _match_one(filter_part, dct, incomplete):
    # TODO: Generalize code with YoutubeDL._build_format_filter
    STRING_OPERATORS = {
        '*=': operator.contains,
        '^=': lambda attr, value: attr.startswith(value),
        '$=': lambda attr, value: attr.endswith(value),
        '~=': lambda attr, value: re.search(value, attr),
    }
    COMPARISON_OPERATORS = {
        **STRING_OPERATORS,
        '<=': operator.le,  # "<=" must be defined above "<"
        '<': operator.lt,
        '>=': operator.ge,
        '>': operator.gt,
        '=': operator.eq,
    }

    if isinstance(incomplete, bool):
        is_incomplete = lambda _: incomplete
    else:
        is_incomplete = lambda k: k in incomplete

    operator_rex = re.compile(r'''(?x)
        (?P<key>[a-z_]+)
        \s*(?P<negation>!\s*)?(?P<op>{})(?P<none_inclusive>\s*\?)?\s*
        (?:
            (?P<quote>["\'])(?P<quotedstrval>.+?)(?P=quote)|
            (?P<strval>.+?)
        )
        '''.format('|'.join(map(re.escape, COMPARISON_OPERATORS.keys()))))
    m = operator_rex.fullmatch(filter_part.strip())
    if m:
        m = m.groupdict()
        unnegated_op = COMPARISON_OPERATORS[m['op']]
        if m['negation']:
            op = lambda attr, value: not unnegated_op(attr, value)
        else:
            op = unnegated_op
        comparison_value = m['quotedstrval'] or m['strval']
        if m['quote']:
            comparison_value = comparison_value.replace(r'\{}'.format(m['quote']), m['quote'])
        actual_value = dct.get(m['key'])
        numeric_comparison = None
        if isinstance(actual_value, (int, float)):
            # If the original field is a string and matching comparisonvalue is
            # a number we should respect the origin of the original field
            # and process comparison value as a string (see
            # https://github.com/ytdl-org/youtube-dl/issues/11082)
            try:
                numeric_comparison = int(comparison_value)
            except ValueError:
                numeric_comparison = parse_filesize(comparison_value)
                if numeric_comparison is None:
                    numeric_comparison = parse_filesize(f'{comparison_value}B')
                if numeric_comparison is None:
                    numeric_comparison = parse_duration(comparison_value)
        if numeric_comparison is not None and m['op'] in STRING_OPERATORS:
            raise ValueError('Operator {} only supports string values!'.format(m['op']))
        if actual_value is None:
            return is_incomplete(m['key']) or m['none_inclusive']
        return op(actual_value, comparison_value if numeric_comparison is None else numeric_comparison)

    UNARY_OPERATORS = {
        '': lambda v: (v is True) if isinstance(v, bool) else (v is not None),
        '!': lambda v: (v is False) if isinstance(v, bool) else (v is None),
    }
    operator_rex = re.compile(r'''(?x)
        (?P<op>{})\s*(?P<key>[a-z_]+)
        '''.format('|'.join(map(re.escape, UNARY_OPERATORS.keys()))))
    m = operator_rex.fullmatch(filter_part.strip())
    if m:
        op = UNARY_OPERATORS[m.group('op')]
        actual_value = dct.get(m.group('key'))
        if is_incomplete(m.group('key')) and actual_value is None:
            return True
        return op(actual_value)

    raise ValueError(f'Invalid filter part {filter_part!r}')