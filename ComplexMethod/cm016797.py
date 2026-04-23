def get_outputs_summary(outputs: dict) -> tuple[int, Optional[dict]]:
    """
    Count outputs and find preview in a single pass.
    Returns (outputs_count, preview_output).

    Preview priority (matching frontend):
    1. type="output" with previewable media
    2. Any previewable media
    """
    count = 0
    preview_output = None
    fallback_preview = None

    for node_id, node_outputs in outputs.items():
        if not isinstance(node_outputs, dict):
            continue
        for media_type, items in node_outputs.items():
            # 'animated' is a boolean flag, not actual output items
            if media_type == 'animated' or not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    # Handle text outputs (non-dict items like strings or tuples)
                    normalized = normalize_output_item(item)
                    if normalized is None:
                        # Not a 3D file string — check for text preview
                        if media_type == 'text':
                            count += 1
                            if preview_output is None:
                                if isinstance(item, tuple):
                                    text_value = item[0] if item else ''
                                else:
                                    text_value = str(item)
                                text_preview = _create_text_preview(text_value)
                                enriched = {
                                    **text_preview,
                                    'nodeId': node_id,
                                    'mediaType': media_type
                                }
                                if fallback_preview is None:
                                    fallback_preview = enriched
                        continue
                    # normalize_output_item returned a dict (e.g. 3D file)
                    item = normalized

                count += 1

                if preview_output is not None:
                    continue

                if is_previewable(media_type, item):
                    enriched = {
                        **item,
                        'nodeId': node_id,
                    }
                    if 'mediaType' not in item:
                        enriched['mediaType'] = media_type
                    if item.get('type') == 'output':
                        preview_output = enriched
                    elif fallback_preview is None:
                        fallback_preview = enriched

    return count, preview_output or fallback_preview