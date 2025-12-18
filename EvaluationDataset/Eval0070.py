def segment_image(image: np.ndarray, thresholds: list[int]) -> np.ndarray:

    segmented = np.zeros_like(image, dtype=np.int32)

    for i, threshold in enumerate(thresholds):
        segmented[image > threshold] = i + 1

    return segmented
