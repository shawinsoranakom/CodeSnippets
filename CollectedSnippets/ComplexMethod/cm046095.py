def get_sample_page_indices(page_count: int, max_pages: int = MAX_SAMPLE_PAGES):
    if page_count <= 0 or max_pages <= 0:
        return []

    sample_count = min(page_count, max_pages)
    if sample_count == page_count:
        return list(range(page_count))
    if sample_count == 1:
        return [0]

    indices = []
    seen = set()
    for i in range(sample_count):
        page_index = round(i * (page_count - 1) / (sample_count - 1))
        page_index = max(0, min(page_count - 1, page_index))
        if page_index not in seen:
            indices.append(page_index)
            seen.add(page_index)

    if len(indices) < sample_count:
        for page_index in range(page_count):
            if page_index in seen:
                continue
            indices.append(page_index)
            seen.add(page_index)
            if len(indices) == sample_count:
                break

    return sorted(indices)