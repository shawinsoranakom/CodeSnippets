def parse_sleep_func(expr):
        NUMBER_RE = r'\d+(?:\.\d+)?'
        op, start, limit, step, *_ = (*tuple(re.fullmatch(
            rf'(?:(linear|exp)=)?({NUMBER_RE})(?::({NUMBER_RE})?)?(?::({NUMBER_RE}))?',
            expr.strip()).groups()), None, None)

        if op == 'exp':
            return lambda n: min(float(start) * (float(step or 2) ** n), float(limit or 'inf'))
        else:
            default_step = start if op or limit else 0
            return lambda n: min(float(start) + float(step or default_step) * n, float(limit or 'inf'))