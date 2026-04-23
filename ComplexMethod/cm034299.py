def join_sentences(first: str | None, second: str | None) -> str:
    """Join two sentences together."""
    first = (first or '').strip()
    second = (second or '').strip()

    if first and first[-1] not in ('!', '?', '.'):
        first += '.'

    if second and second[-1] not in ('!', '?', '.'):
        second += '.'

    if first and not second:
        return first

    if not first and second:
        return second

    return ' '.join((first, second))