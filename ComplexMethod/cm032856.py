def remove_contents_table(sections, eng=False):
    i = 0
    while i < len(sections):
        def get(i):
            nonlocal sections
            return (sections[i] if isinstance(sections[i],
                                              type("")) else sections[i][0]).strip()

        if not re.match(r"(contents|目录|目次|table of contents|致谢|acknowledge)$",
                        re.sub(r"( | |\u3000)+", "", get(i).split("@@")[0], flags=re.IGNORECASE)):
            i += 1
            continue
        sections.pop(i)
        if i >= len(sections):
            break
        prefix = get(i)[:3] if not eng else " ".join(get(i).split()[:2])
        while not prefix:
            sections.pop(i)
            if i >= len(sections):
                break
            prefix = get(i)[:3] if not eng else " ".join(get(i).split()[:2])
        sections.pop(i)
        if i >= len(sections) or not prefix:
            break
        for j in range(i, min(i + 128, len(sections))):
            if not re.match(prefix, get(j)):
                continue
            for _ in range(i, j):
                sections.pop(i)
            break