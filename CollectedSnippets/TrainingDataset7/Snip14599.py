def add_truncation_text(text, truncate=None):
    if truncate is None:
        truncate = pgettext(
            "String to return when truncating text", "%(truncated_text)s…"
        )
    if "%(truncated_text)s" in truncate:
        return truncate % {"truncated_text": text}
    # The truncation text didn't contain the %(truncated_text)s string
    # replacement argument so just append it to the text.
    if text.endswith(truncate):
        # But don't append the truncation text if the current text already ends
        # in this.
        return text
    return f"{text}{truncate}"