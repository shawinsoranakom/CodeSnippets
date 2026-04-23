def get_rotation(
    img: np.ndarray, pt1: np.ndarray, pt2: np.ndarray, rows: int, cols: int
) -> np.ndarray:
    matrix = cv2.getAffineTransform(pt1, pt2)
    return cv2.warpAffine(img, matrix, (rows, cols))
