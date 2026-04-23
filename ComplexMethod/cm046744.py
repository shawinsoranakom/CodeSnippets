def detect_multimodal_dataset(dataset):
    """
    Detects if dataset contains multimodal data (images and/or audio).

    Two-pass approach for each modality:
      1. Column-name heuristic (fast): checks for keywords.
      2. Value-type inspection (reliable): checks actual sample values.

    Returns:
        dict: {
            "is_image": bool,
            "multimodal_columns": list of column names containing image data,
            "modality_types": list of detected types (e.g., ["image", "audio"]),
            "is_audio": bool,
            "audio_columns": list of column names containing audio data,
            "detected_audio_column": str or None,
            "detected_text_column": str or None,
        }
    """
    sample = next(iter(dataset))
    column_names = list(sample.keys())

    # Keywords that indicate image data
    image_keywords = [
        "image",
        "img",
        "pixel",
        "jpg",
        "jpeg",
        "png",
        "webp",
        "bmp",
        "gif",
        "tiff",
        "svg",
        "photo",
        "pic",
        "picture",
        "visual",
        "file_name",
        "filename",
    ]

    # Keywords that indicate audio data
    audio_keywords = ["audio", "speech", "wav", "waveform", "sound"]

    multimodal_columns = []
    audio_columns = []
    modality_types = set()

    # ── Image detection ─────────────────────────────────────
    # Pass 1: column-name heuristic (word-boundary match to avoid
    #          false positives like 'pic' in 'topic')
    for col_name in column_names:
        for keyword in image_keywords:
            if _keyword_in_column(keyword, col_name):
                multimodal_columns.append(col_name)
                modality_types.add(keyword)
                break

    # Pass 2: inspect actual values
    already_detected = set(multimodal_columns)
    for col_name in column_names:
        if col_name in already_detected:
            continue
        value = sample[col_name]
        if _is_image_value(value):
            multimodal_columns.append(col_name)
            modality_types.add("image")

    # ── Audio detection ─────────────────────────────────────
    # Pass 1: column-name heuristic (word-boundary match)
    for col_name in column_names:
        for keyword in audio_keywords:
            if _keyword_in_column(keyword, col_name):
                audio_columns.append(col_name)
                modality_types.add("audio")
                break

    # Pass 2: inspect actual values (catches non-obvious column names)
    already_audio = set(audio_columns)
    for col_name in column_names:
        if col_name in already_audio:
            continue
        value = sample[col_name]
        if _is_audio_value(value):
            audio_columns.append(col_name)
            modality_types.add("audio")

    # Filter out columns that are actually audio from the image list
    # (e.g. a column named "audio" with {"bytes", "path"} could match _is_image_value)
    if audio_columns:
        audio_set = set(audio_columns)
        multimodal_columns = [c for c in multimodal_columns if c not in audio_set]

    # Detect text column for audio datasets
    detected_text_col = None
    if audio_columns:
        text_keywords = ["text", "sentence", "transcript", "transcription", "label"]
        for col_name in column_names:
            if col_name.lower() in text_keywords:
                detected_text_col = col_name
                break

    is_audio = len(audio_columns) > 0

    # Detect speaker_id column for TTS datasets (CSM, Orpheus, Spark)
    detected_speaker_col = None
    if audio_columns:
        speaker_keywords = ["source", "speaker", "speaker_id"]
        for col_name in column_names:
            if col_name.lower() in speaker_keywords:
                detected_speaker_col = col_name
                break

    return {
        "is_image": len(multimodal_columns) > 0,
        "multimodal_columns": multimodal_columns,
        "modality_types": list(modality_types),
        "is_audio": is_audio,
        "audio_columns": audio_columns,
        "detected_audio_column": audio_columns[0] if audio_columns else None,
        "detected_text_column": detected_text_col,
        "detected_speaker_column": detected_speaker_col,
    }