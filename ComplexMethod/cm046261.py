def _infer_ndjson_kpt_shape(image_records: list) -> list:
    """Infer kpt_shape [num_keypoints, dims] from NDJSON pose annotations.

    Scans up to 50 pose annotations across image records. Annotation format is [classId, cx, cy, w, h, kp1_x, kp1_y,
    kp1_vis, ...] so keypoint values start at index 5.

    Tries dims=3 first (x, y, visibility) with visibility validation ({0, 1, 2}), then falls back to dims=2 (x, y only)
    when values are unambiguously not divisible by 3.
    """
    kpt_lengths = []
    samples = []  # raw keypoint value slices for visibility checking
    for record in image_records:
        for ann in record.get("annotations", {}).get("pose", []):
            kpt_len = len(ann) - 5  # subtract classId + bbox (4 values)
            if kpt_len > 0:
                kpt_lengths.append(kpt_len)
                samples.append(ann[5:])
            if len(kpt_lengths) >= 50:
                break
        if len(kpt_lengths) >= 50:
            break

    if not kpt_lengths or len(set(kpt_lengths)) != 1:
        raise ValueError("Pose dataset missing required 'kpt_shape'. See https://docs.ultralytics.com/datasets/pose/")

    n = kpt_lengths[0]

    # Try dims=3: requires divisible by 3 and every 3rd value (visibility) in {0, 1, 2}
    if n % 3 == 0 and all(v in (0, 1, 2) for s in samples for v in s[2::3]):
        return [n // 3, 3]

    # Try dims=2: only when NOT divisible by 3 (avoids misclassifying dims=3 data)
    if n % 2 == 0 and n % 3 != 0:
        return [n // 2, 2]

    raise ValueError("Pose dataset missing required 'kpt_shape'. See https://docs.ultralytics.com/datasets/pose/")