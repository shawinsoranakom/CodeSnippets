def masks2segments(masks: np.ndarray | torch.Tensor, strategy: str = "all") -> list[np.ndarray]:
    """Convert masks to segments using contour detection.

    Args:
        masks (np.ndarray | torch.Tensor): Binary masks with shape (N, H, W).
        strategy (str): Segmentation strategy, either 'all' or 'largest'.

    Returns:
        (list): List of segment masks as float32 arrays.
    """
    from ultralytics.data.converter import merge_multi_segment

    masks = masks.astype("uint8") if isinstance(masks, np.ndarray) else masks.byte().cpu().numpy()
    segments = []
    for x in np.ascontiguousarray(masks):
        c = cv2.findContours(x, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        if c:
            if strategy == "all":  # merge and concatenate all segments
                c = (
                    np.concatenate(merge_multi_segment([x.reshape(-1, 2) for x in c]))
                    if len(c) > 1
                    else c[0].reshape(-1, 2)
                )
            elif strategy == "largest":  # select largest segment
                c = np.array(c[np.array([len(x) for x in c]).argmax()]).reshape(-1, 2)
        else:
            c = np.zeros((0, 2))  # no segments found
        segments.append(c.astype("float32"))
    return segments