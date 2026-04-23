def merge_pdf_positions(sources):
    merged = []
    seen = set()
    for source in sources or []:
        if isinstance(source, dict):
            positions = extract_pdf_positions(source)
        elif isinstance(source, list):
            positions = source
        else:
            positions = []

        for pos in positions:
            if not isinstance(pos, (list, tuple)) or len(pos) < 5:
                continue
            key = tuple(pos[:5])
            if key in seen:
                continue
            seen.add(key)
            merged.append(list(pos[:5]))

    merged.sort(key=lambda item: (item[0], item[3], item[1]))
    return merged