def generate_table_lines(
    table_name: str,
    table: dict[str, str | bool | int | float | list[str | dict[str, str]]],
) -> collections.abc.Iterator[str]:
    SUPPORTED_TYPES = (str, bool, int, float, list)

    yield f'[{table_name}]\n'
    for name, value in table.items():
        if not isinstance(value, SUPPORTED_TYPES):
            raise TypeError(
                f'expected {"/".join(t.__name__ for t in SUPPORTED_TYPES)} value, '
                f'got {type(value).__name__}')

        if not isinstance(value, list):
            yield f'{name} = {json.dumps(value)}\n'
            continue

        yield f'{name} = ['
        if value:
            yield '\n'
        for element in value:
            yield '    '
            if isinstance(element, dict):
                yield '{ ' + ', '.join(f'{k} = {json.dumps(v)}' for k, v in element.items()) + ' }'
            else:
                yield f'"{element}"'
            yield ',\n'
        yield ']\n'
    yield '\n'