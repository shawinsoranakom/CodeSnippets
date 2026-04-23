def draw_pose(image: np.ndarray, detections: np.ndarray, conf: float = 0.25) -> np.ndarray:
    """Draw pose estimation results on the image (in-place, no tracking)."""
    for det in detections:
        score = det[4]
        if score < conf:
            continue

        # Bounding box
        x0, y0, x1, y1 = map(int, det[:4])
        cv2.rectangle(image, (x0, y0), (x1, y1), (0, 255, 0), 2)
        cv2.putText(image, f"{score:.2f}", (x0, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Parse 17 keypoints: columns 6..56, stride 3 (x, y, conf)
        kpts = det[6:].reshape(17, 3)

        # Draw skeleton limbs
        for i, (a, b) in enumerate(COCO_SKELETON):
            kp_a, kp_b = kpts[a - 1], kpts[b - 1]
            if kp_a[2] > 0.5 and kp_b[2] > 0.5:
                color = tuple(int(c) for c in LIMB_COLORS[i][::-1])  # RGB -> BGR
                pt_a = (int(kp_a[0]), int(kp_a[1]))
                pt_b = (int(kp_b[0]), int(kp_b[1]))
                cv2.line(image, pt_a, pt_b, color, 2)

        # Draw keypoints
        for j, kp in enumerate(kpts):
            if kp[2] > 0.5:
                color = tuple(int(c) for c in KPT_COLORS[j][::-1])  # RGB -> BGR
                cv2.circle(image, (int(kp[0]), int(kp[1])), 4, color, -1)

    return image