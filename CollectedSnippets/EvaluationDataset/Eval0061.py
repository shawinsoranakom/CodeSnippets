def binary_mask(
    image_gray: np.ndarray, image_map: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    true_mask, false_mask = image_gray.copy(), image_gray.copy()
    true_mask[image_map == 1] = 1
    false_mask[image_map == 0] = 0

    return true_mask, false_mask
