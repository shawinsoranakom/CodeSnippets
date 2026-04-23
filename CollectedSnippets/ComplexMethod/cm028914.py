def apply_mask_area(
    frame: np.ndarray,
    cutout: np.ndarray,
    box: tuple,
    face_mask: np.ndarray,
    polygon: np.ndarray,
) -> np.ndarray:
    min_x, min_y, max_x, max_y = box
    box_width = max_x - min_x
    box_height = max_y - min_y

    if (
        cutout is None
        or box_width is None
        or box_height is None
        or face_mask is None
        or polygon is None
    ):
        return frame

    try:
        resized_cutout = gpu_resize(cutout, (box_width, box_height))
        roi = frame[min_y:max_y, min_x:max_x]

        if roi.shape != resized_cutout.shape:
            resized_cutout = gpu_resize(
                resized_cutout, (roi.shape[1], roi.shape[0])
            )

        color_corrected_area = apply_color_transfer(resized_cutout, roi)

        # Create mask for the area
        polygon_mask = np.zeros(roi.shape[:2], dtype=np.uint8)

        # Split points for left and right parts if needed
        if len(polygon) > 50:  # Arbitrary threshold to detect if we have multiple parts
            mid_point = len(polygon) // 2
            left_points = polygon[:mid_point] - [min_x, min_y]
            right_points = polygon[mid_point:] - [min_x, min_y]
            cv2.fillPoly(polygon_mask, [left_points], 255)
            cv2.fillPoly(polygon_mask, [right_points], 255)
        else:
            adjusted_polygon = polygon - [min_x, min_y]
            cv2.fillPoly(polygon_mask, [adjusted_polygon], 255)

        # Apply strong initial feathering (GPU-accelerated when available)
        polygon_mask = gpu_gaussian_blur(polygon_mask, (21, 21), 7)

        # Apply additional feathering
        feather_amount = min(
            30,
            box_width // modules.globals.mask_feather_ratio,
            box_height // modules.globals.mask_feather_ratio,
        )
        feathered_mask = cv2.GaussianBlur(
            polygon_mask.astype(np.float32), (0, 0), feather_amount
        )
        max_val = feathered_mask.max()
        if max_val > 1e-6:
            feathered_mask *= np.float32(1.0 / max_val)

        # Apply additional smoothing to the mask edges
        feathered_mask = cv2.GaussianBlur(feathered_mask, (5, 5), 1)

        face_mask_roi = face_mask[min_y:max_y, min_x:max_x]
        combined_mask = feathered_mask * (face_mask_roi.astype(np.float32) * np.float32(1.0 / 255.0))

        combined_mask_3ch = combined_mask[:, :, np.newaxis]
        inv_mask = np.float32(1.0) - combined_mask_3ch
        blended = (
            color_corrected_area * combined_mask_3ch + roi * inv_mask
        ).astype(np.uint8)

        # Apply face mask to blended result
        face_mask_f32 = face_mask_roi[:, :, np.newaxis].astype(np.float32) * np.float32(1.0 / 255.0)
        face_mask_3channel = np.broadcast_to(face_mask_f32, blended.shape)
        final_blend = blended * face_mask_3channel + roi * (np.float32(1.0) - face_mask_3channel)

        frame[min_y:max_y, min_x:max_x] = final_blend.astype(np.uint8)
    except Exception as e:
        pass

    return frame