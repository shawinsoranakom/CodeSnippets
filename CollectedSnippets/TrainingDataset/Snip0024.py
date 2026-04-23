def check_duplicate_links(links: List[str]) -> Tuple[bool, List]:
    """Check for duplicated links.

    Returns a tuple with True or False and duplicate list.
    """

    seen = {}
    duplicates = []
    has_duplicate = False

    for link in links:
        link = link.rstrip('/')
        if link not in seen:
            seen[link] = 1
        else:
            if seen[link] == 1:
                duplicates.append(link)

    if duplicates:
        has_duplicate = True

    return (has_duplicate, duplicates)
