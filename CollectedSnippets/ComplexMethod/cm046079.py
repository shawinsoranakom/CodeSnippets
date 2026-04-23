def _run_grouped_title_leveling(title_block_refs, title_aided_config):
    doc_title_refs = []
    for title_ref in title_block_refs:
        _, block = title_ref
        if block.get("type") == BlockType.DOC_TITLE:
            block["level"] = 1
            doc_title_refs.append(title_ref)

    paragraph_title_groups = _split_paragraph_title_groups(title_block_refs)
    group_levels = []

    if len(paragraph_title_groups) > 1:
        max_workers = min(len(paragraph_title_groups), MAX_TITLE_GROUP_WORKERS)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    _request_paragraph_group_levels,
                    title_group,
                    title_aided_config,
                )
                for title_group in paragraph_title_groups
            ]
            group_levels = [future.result() for future in futures]
    else:
        group_levels = [
            _request_paragraph_group_levels(title_group, title_aided_config)
            for title_group in paragraph_title_groups
        ]

    for title_group, levels_by_index in zip(paragraph_title_groups, group_levels):
        _apply_levels_to_blocks(title_group, levels_by_index)

    _normalize_title_types(doc_title_refs)
    for title_group in paragraph_title_groups:
        _normalize_title_types(title_group)