def make_colon_as_title(sections):
    if not sections:
        return []
    if isinstance(sections[0], type("")):
        return sections
    i = 0
    while i < len(sections):
        txt, layout = sections[i]
        i += 1
        txt = txt.split("@")[0].strip()
        if not txt:
            continue
        if txt[-1] not in ":：":
            continue
        txt = txt[::-1]
        arr = re.split(r"([。？！!?;；]| \.)", txt)
        if len(arr) < 2 or len(arr[1]) < 32:
            continue
        sections.insert(i - 1, (arr[0][::-1], "title"))
        i += 1