def parse_offset_keywords(kws: list[ast.keyword]):
        values = {kw.arg: kw.value.value for kw in kws if isinstance(kw.value, ast.Constant)}
        if len(values) != len(kws):
            return None
        result = ""

        def build(value, suffix, eq=False):
            nonlocal result
            if eq:
                sign = '='
            elif value < 0:
                sign = '-'
                value = -value
            else:
                sign = '+'
            result += f" {sign}{value}{suffix}"

        match values:
            case {'weekday': 0, 'days': days}:
                values.pop('weekday')
                result += ' =monday'
                days -= 1
                if days:
                    values['days'] = days
                else:
                    values.pop('days')

        for name, suffix in (
            ('days', 'd'),
            ('months', 'm'),
            ('years', 'y'),
            ('weeks', 'w'),
            ('hours', 'H'),
            ('minutes', 'M'),
            ('seconds', 'S'),
        ):
            if value := values.pop(name, None):
                build(value, suffix)
        for name, suffix in (
            ('day', 'd'),
            ('month', 'm'),
            ('year', 'y'),
            ('hour', 'H'),
            ('minute', 'M'),
            ('second', 'S'),
        ):
            if value := values.pop(name, None):
                build(value, suffix, eq=True)
        if values:
            # not everything was parsed
            return None
        return result