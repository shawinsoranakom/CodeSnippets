def _iter_differences(got, expected, field):
    if isinstance(expected, str):
        op, _, val = expected.partition(':')
        if op in ('mincount', 'maxcount', 'count'):
            if not isinstance(got, (list, dict)):
                yield field, f'expected either {list.__name__} or {dict.__name__}, got {type(got).__name__}'
                return

            expected_num = int(val)
            got_num = len(got)
            if op == 'mincount':
                if got_num < expected_num:
                    yield field, f'expected at least {val} items, got {got_num}'
                return

            if op == 'maxcount':
                if got_num > expected_num:
                    yield field, f'expected at most {val} items, got {got_num}'
                return

            assert op == 'count'
            if got_num != expected_num:
                yield field, f'expected exactly {val} items, got {got_num}'
            return

        if not isinstance(got, str):
            yield field, f'expected {str.__name__}, got {type(got).__name__}'
            return

        if op == 're':
            if not re.match(val, got):
                yield field, f'should match {val!r}, got {got!r}'
            return

        if op == 'startswith':
            if not got.startswith(val):
                yield field, f'should start with {val!r}, got {got!r}'
            return

        if op == 'contains':
            if not val.startswith(got):
                yield field, f'should contain {val!r}, got {got!r}'
            return

        if op == 'md5':
            hash_val = md5(got)
            if hash_val != val:
                yield field, f'expected hash {val}, got {hash_val}'
            return

        if got != expected:
            yield field, f'expected {expected!r}, got {got!r}'
        return

    if isinstance(expected, dict) and isinstance(got, dict):
        for key, expected_val in expected.items():
            if key not in got:
                yield field, f'missing key: {key!r}'
                continue

            field_name = key if field is None else f'{field}.{key}'
            yield from _iter_differences(got[key], expected_val, field_name)
        return

    if isinstance(expected, type):
        if not isinstance(got, expected):
            yield field, f'expected {expected.__name__}, got {type(got).__name__}'
        return

    if isinstance(expected, list) and isinstance(got, list):
        # TODO: clever diffing algorithm lmao
        if len(expected) != len(got):
            yield field, f'expected length of {len(expected)}, got {len(got)}'
            return

        for index, (got_val, expected_val) in enumerate(zip(got, expected, strict=True)):
            field_name = str(index) if field is None else f'{field}.{index}'
            yield from _iter_differences(got_val, expected_val, field_name)
        return

    if got != expected:
        yield field, f'expected {expected!r}, got {got!r}'