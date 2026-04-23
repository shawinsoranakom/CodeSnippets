def extract_leading_emoji(text: str) -> Tuple[str, str]:
    """Return a tuple containing the first emoji found in the given string and
    the rest of the string (minus an optional separator between the two).
    """
    re_match = re.search(EMOJI_EXTRACTION_REGEX, text)
    if re_match is None:
        return "", text

    # This cast to Any+type annotation weirdness is done because
    # cast(re.Match[str], ...) explodes at runtime since Python interprets it
    # as an attempt to index into re.Match instead of as a type annotation.
    re_match: re.Match[str] = cast(Any, re_match)
    return re_match.group(1), re_match.group(2)