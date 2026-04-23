def _split_text_with_regex(
    text: str, separator: str, *, keep_separator: bool | Literal["start", "end"]
) -> list[str]:
    # Now that we have the separator, split the text
    if separator:
        if keep_separator:
            # The parentheses in the pattern keep the delimiters in the result.
            splits_ = re.split(f"({separator})", text)
            splits = (
                ([splits_[i] + splits_[i + 1] for i in range(0, len(splits_) - 1, 2)])
                if keep_separator == "end"
                else ([splits_[i] + splits_[i + 1] for i in range(1, len(splits_), 2)])
            )
            if len(splits_) % 2 == 0:
                splits += splits_[-1:]
            splits = (
                ([*splits, splits_[-1]])
                if keep_separator == "end"
                else ([splits_[0], *splits])
            )
        else:
            splits = re.split(separator, text)
    else:
        splits = list(text)
    return [s for s in splits if s]