def parse_index_block(index_block: dict):
    """
    递归解析嵌套索引结构（目录），生成与list一致的blocks结构。

    Args:
        index_block: 索引块字典

    Returns:
        解析后的索引block字典，若内容为空则返回 None
    """
    content = index_block.get("content", [])
    if not content:
        return None

    blocks = []

    for item in content:
        item_type = item.get("type", "")

        if item_type == "text":
            text_content = item.get("content", "")
            spans = parse_text_block_spans(text_content)
            text_block = {
                "type": BlockType.TEXT,
                "lines": [{"spans": spans}]
            }
            anchor = item.get("anchor")
            if isinstance(anchor, str) and anchor.strip():
                text_block["anchor"] = anchor.strip()
            blocks.append(text_block)

        elif item_type == "index":
            nested_index = parse_index_block(item)
            if nested_index:
                blocks.append(nested_index)

    result = {
        "type": BlockType.INDEX,
        "ilevel": index_block.get("ilevel", 0),
        "blocks": blocks
    }

    return result