def table_a_raza(header: tuple[str, ...], rows: list[tuple[str, ...]]) -> collections.abc.Generator[str]:
    widths = [len(col) for col in header]

    for row in rows:
        for index, (width, col) in enumerate(zip(widths, row, strict=True)):
            if len(col) > width:
                widths[index] = len(col)

    yield ' | '.join(col.ljust(width) for width, col in zip(widths, header, strict=True))
    yield '-|-'.join(''.ljust(width, '-') for width in widths)
    for row in rows:
        yield ' | '.join(col.ljust(width) for width, col in zip(widths, row, strict=True))