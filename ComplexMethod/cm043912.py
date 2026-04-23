def is_bop_suffix_only(text: str) -> bool:
    """Check if text is only a BOP-style suffix that lacks meaningful context.

    Returns True if the text is just:
    - Net, Credit, Debit, Assets, Liabilities (with optional parenthetical)
    - Credit/Revenue, Debit/Expenditure
    - These terms should NOT stand alone as titles
    - Or if it starts with a lowercase word/preposition (fragment of larger phrase)

    Parameters
    ----------
    text : str
        The text to check.

    Returns
    -------
    bool
        True if text is just a BOP suffix without meaningful context.
    """
    if not text:
        return False

    # Normalize: strip leading comma/space, and trailing parenthetical
    normalized = text.lstrip(", :")
    if not normalized:
        return True

    # Check if starts with lowercase (indicates a fragment, not a proper category)
    # e.g., "excluding reserves and related items, Net" is a fragment
    first_word = normalized.split()[0] if normalized.split() else ""
    # If first word is lowercase and not a number, it's a fragment
    if first_word and first_word[0].islower() and not first_word[0].isdigit():
        return True

    # Strip trailing parenthetical for BOP term check
    check_text = normalized
    if check_text.endswith(")"):
        paren_start = check_text.rfind(" (")
        if paren_start > 0:
            check_text = check_text[:paren_start].strip()

    # Check if what remains is just a BOP suffix term
    bop_only_terms = {
        "net",
        "credit",
        "debit",
        "assets",
        "liabilities",
        "credit/revenue",
        "debit/expenditure",
        "assets (excl. reserves)",
        "liabilities (incl. net incurrence)",
    }
    return check_text.lower() in bop_only_terms