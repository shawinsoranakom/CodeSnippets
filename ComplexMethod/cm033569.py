def _check_messages(
    label: str,
    patterns: list[str] | str | None,
    entries: list[_messages.WarningSummary] | list[_messages.DeprecationSummary],
    allow_unmatched_message: bool,
) -> None:
    if patterns is None:
        return

    if isinstance(patterns, str):
        patterns = [patterns]

    unmatched = set(str(entry) for entry in entries)

    for pattern in patterns:
        matched = False

        for entry in entries:
            str_entry = str(entry)

            if re.search(pattern, str_entry):
                unmatched.discard(str_entry)
                matched = True

        assert matched, f"{label} pattern {pattern!r} did not match."

    if not allow_unmatched_message:
        assert not unmatched, f"{label} unmatched: {unmatched}"