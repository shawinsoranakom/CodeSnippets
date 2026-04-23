def apply_diff(
    diff: diffobj, text: str | list[str], reverse: bool = False, use_patch: bool = False
) -> list[str]:
    lines = text.splitlines() if isinstance(text, str) else list(text)

    if use_patch:
        lines, _ = _apply_diff_with_subprocess(diff, lines, reverse)
        return lines

    n_lines = len(lines)

    changes = _reverse(diff.changes) if reverse else diff.changes
    # check that the source text matches the context of the diff
    for old, new, line, hunk in changes:
        # might have to check for line is None here for ed scripts
        if old is not None and line is not None:
            if old > n_lines:
                raise HunkApplyException(
                    'context line {n}, "{line}" does not exist in source'.format(
                        n=old, line=line
                    ),
                    hunk=hunk,
                )
            if lines[old - 1] != line:
                # Try to normalize whitespace by replacing multiple spaces with a single space
                # This helps with patches that have different indentation levels
                normalized_line = ' '.join(line.split())
                normalized_source = ' '.join(lines[old - 1].split())
                if normalized_line != normalized_source:
                    raise HunkApplyException(
                        'context line {n}, "{line}" does not match "{sl}"'.format(
                            n=old, line=line, sl=lines[old - 1]
                        ),
                        hunk=hunk,
                    )

    # for calculating the old line
    r = 0
    i = 0

    for old, new, line, hunk in changes:
        if old is not None and new is None:
            del lines[old - 1 - r + i]
            r += 1
        elif old is None and new is not None:
            lines.insert(new - 1, line)
            i += 1
        elif old is not None and new is not None:
            # Sometimes, people remove hunks from patches, making these
            # numbers completely unreliable. Because they're jerks.
            pass

    return lines