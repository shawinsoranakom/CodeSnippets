def draw_tracked_poses(image: np.ndarray, tracked_poses: list) -> np.ndarray:
    """Draw tracked pose results: bbox with track ID color, skeleton, and keypoints (in-place)."""
    for tracked in tracked_poses:
        color = get_track_color(tracked.track_id)

        # Bounding box
        bbox = tracked.predicted_bbox
        x0, y0, x1, y1 = int(bbox.x0), int(bbox.y0), int(bbox.x1), int(bbox.y1)
        cv2.rectangle(image, (x0, y0), (x1, y1), color, 2)
        cv2.putText(image, f"ID {tracked.track_id}", (x0, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Access keypoints from the original PoseObject via tracked.tracked
        pose = tracked.tracked
        if not hasattr(pose, "keypoints") or not pose.keypoints:
            continue

        kpts = pose.keypoints

        # Draw skeleton limbs in track color (links skeleton to its box visually)
        for i, (a, b) in enumerate(COCO_SKELETON):
            kp_a, kp_b = kpts[a - 1], kpts[b - 1]
            if kp_a.confidence > 0.5 and kp_b.confidence > 0.5:
                pt_a = (int(kp_a.x), int(kp_a.y))
                pt_b = (int(kp_b.x), int(kp_b.y))
                cv2.line(image, pt_a, pt_b, color, 2)

        # Draw keypoints
        for j, kp in enumerate(kpts):
            if kp.confidence > 0.5:
                cv2.circle(image, (int(kp.x), int(kp.y)), 4, tuple(int(c) for c in KPT_COLORS[j][::-1]), -1)

    return image