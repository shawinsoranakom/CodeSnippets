def title_frequency(bull, sections):
    bullets_size = len(BULLET_PATTERN[bull])
    levels = [bullets_size + 1 for _ in range(len(sections))]
    if not sections or bull < 0:
        return bullets_size + 1, levels

    for i, (txt, layout) in enumerate(sections):
        for j, p in enumerate(BULLET_PATTERN[bull]):
            if re.match(p, txt.strip()) and not not_bullet(txt):
                levels[i] = j
                break
        else:
            if re.search(r"(title|head)", layout) and not not_title(txt.split("@")[0]):
                levels[i] = bullets_size
    most_level = bullets_size + 1
    for level, c in sorted(Counter(levels).items(), key=lambda x: x[1] * -1):
        if level <= bullets_size:
            most_level = level
            break
    return most_level, levels