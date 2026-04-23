def parse_value(data: str, index: int):
    if data[index] == '[':
        result = []

        indices = parse_enclosed(data, index, ']', LIST_WS_RE)
        valid, index = next(indices)
        while valid:
            index, value = parse_value(data, index)
            result.append(value)
            valid, index = indices.send(index)

        return index, result

    if data[index] == '{':
        result = {}

        indices = parse_enclosed(data, index, '}', WS_RE)
        valid, index = next(indices)
        while valid:
            valid, index = indices.send(parse_kv_pair(data, index, result))

        return index, result

    if match := STRING_RE.match(data, index):
        return match.end(), json.loads(match[0]) if match[0][0] == '"' else match[0][1:-1]

    match = LEFTOVER_VALUE_RE.match(data, index)
    assert match
    value = match[0].strip()
    for func in [
        int,
        float,
        dt.time.fromisoformat,
        dt.date.fromisoformat,
        dt.datetime.fromisoformat,
        {'true': True, 'false': False}.get,
    ]:
        try:
            value = func(value)
            break
        except Exception:
            pass

    return match.end(), value