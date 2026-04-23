def tree_merge(bull, sections, depth):
    if not sections or bull < 0:
        return sections
    if isinstance(sections[0], type("")):
        sections = [(s, "") for s in sections]

    # filter out position information in pdf sections
    sections = [(t, o) for t, o in sections if
                t and len(t.split("@")[0].strip()) > 1 and not re.match(r"[0-9]+$", t.split("@")[0].strip())]

    def get_level(bull, section):
        text, layout = section
        text = re.sub(r"\u3000", " ", text).strip()

        for i, title in enumerate(BULLET_PATTERN[bull]):
            if re.match(title, text.strip()):
                return i + 1, text
        else:
            if re.search(r"(title|head)", layout) and not not_title(text):
                return len(BULLET_PATTERN[bull]) + 1, text
            else:
                return len(BULLET_PATTERN[bull]) + 2, text

    level_set = set()
    lines = []
    for section in sections:
        level, text = get_level(bull, section)
        if not text.strip("\n"):
            continue

        lines.append((level, text))
        level_set.add(level)

    sorted_levels = sorted(list(level_set))

    if depth <= len(sorted_levels):
        target_level = sorted_levels[depth - 1]
    else:
        target_level = sorted_levels[-1]

    if target_level == len(BULLET_PATTERN[bull]) + 2:
        target_level = sorted_levels[-2] if len(sorted_levels) > 1 else sorted_levels[0]

    root = Node(level=0, depth=target_level, texts=[])
    root.build_tree(lines)

    return [element for element in root.get_tree() if element]