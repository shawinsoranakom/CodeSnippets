def draw_segmentation(image: np.ndarray, detections: np.ndarray, masks: list, conf: float = 0.25) -> np.ndarray:
    """Draw instance segmentation results on the image.

    proto_to_mask() returns bbox-cropped masks at prototype resolution. Each mask must be resized to its detection's
    bounding box and placed at the correct image coordinates.
    """
    overlay = image.copy()  # one copy for mask blending
    h, w = image.shape[:2]

    for i, det in enumerate(detections):
        score = det[4]
        if score < conf:
            continue

        class_id = int(det[5])
        color = CLASS_COLORS[class_id % len(CLASS_COLORS)]
        name = COCO_NAMES[class_id] if class_id < len(COCO_NAMES) else str(class_id)

        # Bounding box (clipped to image bounds)
        x0, y0, x1, y1 = map(int, det[:4])
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(w, x1), min(h, y1)

        # Semi-transparent mask overlay: resize bbox-cropped mask and place it
        if i < len(masks):
            mask = masks[i]
            if mask.ndim == 2 and (x1 - x0) > 0 and (y1 - y0) > 0:
                mask_resized = cv2.resize(mask, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
                overlay[y0:y1, x0:x1][mask_resized > 127] = color

        # Bounding box
        cv2.rectangle(image, (x0, y0), (x1, y1), color, 2)

        # Label
        label = f"{name} {score:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(image, (x0, y0 - th - 4), (x0 + tw, y0), color, -1)
        cv2.putText(image, label, (x0, y0 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Blend mask overlay
    cv2.addWeighted(overlay, 0.4, image, 0.6, 0, image)
    return image