def enhance_media_sections_with_vision(
    sections,
    tenant_id,
    vlm_conf=None,
    callback=None,
):
    if not sections or not tenant_id:
        return sections

    try:
        try:
            vision_model_config = get_model_config_by_type_and_name(
                tenant_id, LLMType.IMAGE2TEXT, vlm_conf["llm_id"]
            )
        except Exception:
            vision_model_config = get_tenant_default_model_by_type(
                tenant_id, LLMType.IMAGE2TEXT
            )
        vision_model = LLMBundle(tenant_id, vision_model_config)
    except Exception:
        return sections

    for item in sections:
        if item.get("doc_type_kwd") not in {"image", "table"}:
            continue
        if item.get("image") is None:
            continue

        text = item.get("text") or ""
        try:
            parsed = VisionFigureParser(
                vision_model=vision_model,
                figures_data=[((item["image"], [""]), [(0, 0, 0, 0, 0)])],
                context_size=0,
            )(callback=callback)
        except Exception:
            continue

        if not parsed:
            continue

        # VisionFigureParser returns [((image, text_or_text_list), positions), ...].
        first_result = parsed[0]
        # first_result[0] is the (image, parsed_text) tuple.
        image_and_text = first_result[0]
        # image_and_text[1] is the parsed text content.
        parsed_text = str(image_and_text[1] or "").strip()

        if parsed_text:
            item["text"] = f"{text}\n{parsed_text}" if text else parsed_text

    return sections