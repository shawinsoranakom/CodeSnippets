def tabulate_2d(elements: Sequence[Sequence[T]], headers: Sequence[T]) -> str:
    widths = [len(str(e)) for e in headers]
    for row in elements:
        assert len(row) == len(headers)
        for i, e in enumerate(row):
            widths[i] = max(widths[i], len(str(e)))
    lines = []
    lines.append("|".join(f" {h:{w}} " for h, w in zip(headers, widths)))
    #              widths          whitespace      horizontal separators
    total_width = sum(widths) + (len(widths) * 2) + (len(widths) - 1)
    lines.append("-" * total_width)
    for row in elements:
        lines.append("|".join(f" {e:{w}} " for e, w in zip(row, widths)))
    return "\n".join(lines)