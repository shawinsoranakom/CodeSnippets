def remove_small_regions(mask: np.ndarray, area_thresh: float, mode: str) -> tuple[np.ndarray, bool]:
    """Remove small disconnected regions or holes in a mask based on area threshold and mode.

    Args:
        mask (np.ndarray): Binary mask to process.
        area_thresh (float): Area threshold below which regions will be removed.
        mode (str): Processing mode, either 'holes' to fill small holes or 'islands' to remove small disconnected
            regions.

    Returns:
        processed_mask (np.ndarray): Processed binary mask with small regions removed.
        modified (bool): Whether any regions were modified.

    Examples:
        >>> mask = np.zeros((100, 100), dtype=np.bool_)
        >>> mask[40:60, 40:60] = True  # Create a square
        >>> mask[45:55, 45:55] = False  # Create a hole
        >>> processed_mask, modified = remove_small_regions(mask, 50, "holes")
    """
    import cv2  # type: ignore

    assert mode in {"holes", "islands"}, f"Provided mode {mode} is invalid"
    correct_holes = mode == "holes"
    working_mask = (correct_holes ^ mask).astype(np.uint8)
    n_labels, regions, stats, _ = cv2.connectedComponentsWithStats(working_mask, 8)
    sizes = stats[:, -1][1:]  # Row 0 is background label
    small_regions = [i + 1 for i, s in enumerate(sizes) if s < area_thresh]
    if not small_regions:
        return mask, False
    fill_labels = [0, *small_regions]
    if not correct_holes:
        # If every region is below threshold, keep largest
        fill_labels = [i for i in range(n_labels) if i not in fill_labels] or [int(np.argmax(sizes)) + 1]
    mask = np.isin(regions, fill_labels)
    return mask, True