def _clean_paragraphs(txt):
    paragraphs = txt.split("\n\n")
    cleaned_paragraphs = [_clean(x) for x in paragraphs]
    return cleaned_paragraphs