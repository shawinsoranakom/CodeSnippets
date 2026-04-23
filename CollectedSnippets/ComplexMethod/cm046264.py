def draw_specific_kpts(
        self,
        keypoints: list[list[float]],
        indices: list[int] | None = None,
        radius: int = 2,
        conf_thresh: float = 0.25,
    ) -> np.ndarray:
        """Draw specific keypoints for gym steps counting.

        Args:
            keypoints (list[list[float]]): Keypoints data to be plotted, each in format [x, y, confidence].
            indices (list[int], optional): Keypoint indices to be plotted. The drawing order follows the order of this
                list.
            radius (int): Keypoint radius.
            conf_thresh (float): Confidence threshold for keypoints.

        Returns:
            (np.ndarray): Image with drawn keypoints.

        Notes:
            Keypoint format: [x, y] or [x, y, confidence].
            Modifies self.im in-place.
        """
        indices = indices or [2, 5, 7]
        n = len(keypoints)
        points = [
            (int(keypoints[j][0]), int(keypoints[j][1]))
            for j in indices
            if 0 <= j < n and (float(keypoints[j][2]) if len(keypoints[j]) > 2 else 1.0) >= conf_thresh
        ]

        # Draw lines between consecutive points
        for start, end in zip(points[:-1], points[1:]):
            cv2.line(self.im, start, end, (0, 255, 0), 2, lineType=cv2.LINE_AA)

        # Draw circles for keypoints
        for pt in points:
            cv2.circle(self.im, pt, radius, (0, 0, 255), -1, lineType=cv2.LINE_AA)

        return self.im