def parse_search_query(query: str) -> list[list[str]]:
    """
    Parse a search query string into OR-groups of AND-terms.

    Supports:
    - Quoted phrases: "exact phrase"
    - OR operator: term1 | term2
    - AND operator (implicit or +): term1 term2, term1+term2
    - Stop words are filtered out (of, the, a, an, is, are, in, on, for, with, and, or)

    Examples
    --------
    >>> parse_search_query('inflation | "consumer price"')
    [['inflation'], ['consumer price']]
    >>> parse_search_query('gdp growth')
    [['gdp', 'growth']]
    """
    # pylint: disable=import-outside-toplevel
    import string as string_module

    STOP_WORDS = {  # pylint: disable=C0103
        "of",
        "the",
        "a",
        "an",
        "is",
        "are",
        "in",
        "on",
        "for",
        "with",
        "and",
        "or",
    }
    or_groups: list = []
    parts_by_or = [p.strip() for p in query.split("|")]

    for or_part in parts_by_or:
        if not or_part:
            continue

        current_and_group: list = []
        in_quote = False
        current_term: list = []

        # Add a space at the end to ensure the last term is processed
        for char in or_part + " ":
            if char == '"':
                if in_quote:
                    # End of a quoted term
                    if current_term:
                        term = "".join(current_term).lower()
                        current_and_group.append(term)
                        current_term = []
                    in_quote = False
                else:
                    # Start of a quoted term
                    if current_term:  # process term before quote
                        term = (
                            "".join(current_term)
                            .lower()
                            .strip(string_module.punctuation)
                        )
                        if term and term not in STOP_WORDS:
                            current_and_group.append(term)
                        current_term = []
                    in_quote = True
            elif (char == "+" or char.isspace()) and not in_quote:
                # End of a non-quoted term
                if current_term:
                    term = (
                        "".join(current_term).lower().strip(string_module.punctuation)
                    )
                    if term and term not in STOP_WORDS:
                        current_and_group.append(term)
                    current_term = []
            else:
                current_term.append(char)

        if current_and_group:
            or_groups.append(current_and_group)

    return or_groups