def replace_inline_table_images(
    blocks: list[dict],
    image_writer,
    page_index: int,
    table_block_type=BlockType.TABLE,
    table_body_type=BlockType.TABLE_BODY,
    table_span_type=ContentType.TABLE,
) -> None:
    """Persist inline base64 images embedded inside table HTML."""
    if not image_writer:
        return

    for block in blocks:
        if block.get("type") != table_block_type:
            continue

        for sub_block in block.get("blocks", []):
            if sub_block.get("type") != table_body_type:
                continue

            for line in sub_block.get("lines", []):
                for span in line.get("spans", []):
                    if span.get("type") != table_span_type:
                        continue
                    span["html"] = replace_inline_base64_img_src(
                        span.get("html", ""),
                        image_writer,
                        page_index,
                    )