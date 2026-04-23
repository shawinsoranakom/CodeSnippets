def can_merge_text_blocks(current_block, previous_block, current_metric_lines=None, previous_metric_lines=None):
    current_lines = current_block.get("lines", [])
    previous_lines = previous_block.get("lines", [])
    if not current_lines or not previous_lines:
        return False

    current_metric_lines = current_metric_lines or current_lines
    previous_metric_lines = previous_metric_lines or previous_lines
    if not current_metric_lines or not previous_metric_lines:
        return False

    first_metric_line = current_metric_lines[0]
    first_line_height = _line_height(first_metric_line)
    if first_line_height <= 0:
        return False

    current_bbox_fs = _build_bbox_fs(current_block, current_metric_lines)
    if abs(current_bbox_fs[0] - first_metric_line["bbox"][0]) >= first_line_height / 2:
        return False

    last_metric_line = previous_metric_lines[-1]
    last_line_height = _line_height(last_metric_line)
    if last_line_height <= 0:
        return False

    previous_bbox_fs = _build_bbox_fs(previous_block, previous_metric_lines)

    first_span = _first_span(current_lines[0])
    last_span = _last_span(previous_lines[-1])
    if first_span is None or last_span is None:
        return False

    first_content = first_span.get("content", "")
    last_content = last_span.get("content", "")
    if not first_content:
        return False

    current_block_width = current_block["bbox"][2] - current_block["bbox"][0]
    previous_block_width = previous_block["bbox"][2] - previous_block["bbox"][0]
    min_block_width = min(current_block_width, previous_block_width)
    if min_block_width <= 0:
        return False

    if abs(previous_bbox_fs[2] - last_metric_line["bbox"][2]) >= last_line_height:
        return False
    if last_content.endswith(LINE_STOP_FLAG):
        return False
    if abs(current_block_width - previous_block_width) >= min_block_width:
        return False
    if first_content[0].isdigit() or first_content[0].isupper():
        return False
    if current_block["bbox"][1] >= previous_block["bbox"][3]:
        return False
    if len(current_metric_lines) <= 1 and len(previous_metric_lines) <= 1:
        return False

    return True