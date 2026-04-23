def _pop_index_and_sub_index(block: dict) -> dict:
    """When streaming, `langchain-core` uses `index` to aggregate text blocks.

    OpenAI API does not support this key, so we need to remove it.
    """
    new_block = {k: v for k, v in block.items() if k != "index"}
    if "summary" in new_block and isinstance(new_block["summary"], list):
        new_summary = []
        for sub_block in new_block["summary"]:
            new_sub_block = {k: v for k, v in sub_block.items() if k != "index"}
            new_summary.append(new_sub_block)
        new_block["summary"] = new_summary
    return new_block