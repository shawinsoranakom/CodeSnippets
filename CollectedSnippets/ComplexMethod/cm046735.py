def check_dataset_format(dataset, is_vlm: bool = False) -> dict:
    """
    Lightweight format check without processing - for frontend validation.

    Use this to quickly determine if user needs to manually map columns
    before calling the full format_and_template_dataset().

    Args:
        dataset: HuggingFace dataset
        is_vlm: Whether this is a Vision-Language Model dataset

    Returns:
        dict: {
            "requires_manual_mapping": bool - True if user must map columns,
            "detected_format": str - The detected format,
            "columns": list - Available column names for mapping UI,
            "suggested_mapping": dict or None - Auto-detected mapping if available,
            "detected_image_column": str or None - For VLM only,
            "detected_text_column": str or None - For VLM only,
        }
    """
    columns = (
        list(dataset.column_names)
        if hasattr(dataset, "column_names")
        else list(next(iter(dataset)).keys())
    )

    # Auto-detect multimodal data regardless of is_vlm flag
    multimodal_info = detect_multimodal_dataset(dataset)
    is_audio = multimodal_info.get("is_audio", False)

    # Common audio fields for all return paths
    audio_fields = {
        "is_audio": is_audio,
        "detected_audio_column": multimodal_info.get("detected_audio_column"),
        "detected_speaker_column": multimodal_info.get("detected_speaker_column"),
    }

    if is_vlm:
        vlm_structure = detect_vlm_dataset_structure(dataset)
        requires_mapping = vlm_structure["format"] == "unknown"

        warning = None
        if requires_mapping:
            img_col = vlm_structure.get("image_column")
            txt_col = vlm_structure.get("text_column")
            missing = []
            if not img_col:
                missing.append("image")
            if not txt_col:
                missing.append("text")
            if missing:
                warning = (
                    f"Could not auto-detect {' or '.join(missing)} column. "
                    "Please assign image and text columns manually."
                )

        return {
            "requires_manual_mapping": requires_mapping,
            "detected_format": vlm_structure["format"],
            "columns": columns,
            "suggested_mapping": None,
            "detected_image_column": vlm_structure.get("image_column"),
            "detected_text_column": vlm_structure.get("text_column"),
            "is_image": multimodal_info["is_image"],
            "multimodal_columns": multimodal_info.get("multimodal_columns"),
            "warning": warning,
            **audio_fields,
        }

    if is_audio:
        # Audio dataset — require manual mapping only when columns can't be auto-detected
        detected_audio = multimodal_info.get("detected_audio_column")
        detected_text = multimodal_info.get("detected_text_column")
        needs_mapping = not detected_audio or not detected_text
        return {
            "requires_manual_mapping": needs_mapping,
            "detected_format": "audio",
            "columns": columns,
            "suggested_mapping": None,
            "detected_image_column": None,
            "detected_text_column": multimodal_info.get("detected_text_column"),
            "is_image": False,
            "multimodal_columns": multimodal_info.get("audio_columns"),
            **audio_fields,
        }

    # Text / LLM flow
    detected = detect_dataset_format(dataset)

    # If format is unknown, try heuristic detection
    if detected["format"] == "unknown":
        heuristic_mapping = detect_custom_format_heuristic(dataset)
        if heuristic_mapping:
            return {
                "requires_manual_mapping": False,
                "detected_format": "custom_heuristic",
                "columns": columns,
                "suggested_mapping": heuristic_mapping,
                "detected_image_column": None,
                "detected_text_column": None,
                "is_image": multimodal_info["is_image"],
                "multimodal_columns": multimodal_info.get("multimodal_columns"),
                **audio_fields,
            }
        else:
            # Heuristic failed — user must map manually (or use AI Assist)
            return {
                "requires_manual_mapping": True,
                "detected_format": "unknown",
                "columns": columns,
                "suggested_mapping": None,
                "detected_image_column": None,
                "detected_text_column": None,
                "is_image": multimodal_info["is_image"],
                "multimodal_columns": multimodal_info.get("multimodal_columns"),
                "warning": (
                    f"Could not auto-detect column roles for columns: {columns}. "
                    "Please assign roles manually, or use AI Assist."
                ),
                **audio_fields,
            }

    # Known format detected
    return {
        "requires_manual_mapping": False,
        "detected_format": detected["format"],
        "columns": columns,
        "suggested_mapping": None,
        "detected_image_column": None,
        "detected_text_column": None,
        "is_image": multimodal_info["is_image"],
        "multimodal_columns": multimodal_info.get("multimodal_columns"),
        **audio_fields,
    }