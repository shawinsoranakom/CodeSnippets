def _link_index_entries_by_anchor(middle_json: dict) -> None:
    """Keep TOC anchors only when they exist on parsed body blocks."""
    pdf_info = middle_json.get("pdf_info", [])
    valid_anchors: set[str] = set()

    for page_info in pdf_info:
        for block in page_info.get("para_blocks", []):
            anchor = block.get("anchor")
            if isinstance(anchor, str) and anchor.strip():
                valid_anchors.add(anchor.strip())

    if not valid_anchors:
        return

    for page_info in pdf_info:
        for block in page_info.get("para_blocks", []):
            if block.get("type") != BlockType.INDEX:
                continue
            toc_text_blocks: list[dict] = []
            _collect_index_text_blocks(block, toc_text_blocks)
            for text_block in toc_text_blocks:
                anchor = text_block.get("anchor")
                if not isinstance(anchor, str):
                    text_block.pop("anchor", None)
                    continue
                anchor = anchor.strip()
                if not anchor or anchor not in valid_anchors:
                    text_block.pop("anchor", None)
                    continue
                text_block["anchor"] = anchor