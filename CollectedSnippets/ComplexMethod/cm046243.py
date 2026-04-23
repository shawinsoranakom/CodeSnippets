def _mosaic4(self, labels: dict[str, Any]) -> dict[str, Any]:
        """Create a 2x2 image mosaic from four input images.

        This method combines four images into a single mosaic image by placing them in a 2x2 grid. It also updates the
        corresponding labels for each image in the mosaic.

        Args:
            labels (dict[str, Any]): A dictionary containing image data and labels for the base image (index 0) and
                three additional images (indices 1-3) in the 'mix_labels' key.

        Returns:
            (dict[str, Any]): A dictionary containing the mosaic image and updated labels. The 'img' key contains the
                mosaic image as a numpy array, and other keys contain the combined and adjusted labels for all
                four images.

        Examples:
            >>> mosaic = Mosaic(dataset, imgsz=640, p=1.0, n=4)
            >>> labels = {
            ...     "img": np.random.rand(480, 640, 3),
            ...     "mix_labels": [{"img": np.random.rand(480, 640, 3)} for _ in range(3)],
            ... }
            >>> result = mosaic._mosaic4(labels)
            >>> assert result["img"].shape == (1280, 1280, 3)
        """
        mosaic_labels = []
        s = self.imgsz
        yc, xc = (int(random.uniform(-x, 2 * s + x)) for x in self.border)  # mosaic center x, y
        for i in range(4):
            labels_patch = labels if i == 0 else labels["mix_labels"][i - 1]
            # Load image
            img = labels_patch["img"]
            h, w = labels_patch.pop("resized_shape")

            # Place img in img4
            if i == 0:  # top left
                img4 = np.full((s * 2, s * 2, img.shape[2]), 114, dtype=np.uint8)  # base image with 4 tiles
                x1a, y1a, x2a, y2a = max(xc - w, 0), max(yc - h, 0), xc, yc  # xmin, ymin, xmax, ymax (large image)
                x1b, y1b, x2b, y2b = w - (x2a - x1a), h - (y2a - y1a), w, h  # xmin, ymin, xmax, ymax (small image)
            elif i == 1:  # top right
                x1a, y1a, x2a, y2a = xc, max(yc - h, 0), min(xc + w, s * 2), yc
                x1b, y1b, x2b, y2b = 0, h - (y2a - y1a), min(w, x2a - x1a), h
            elif i == 2:  # bottom left
                x1a, y1a, x2a, y2a = max(xc - w, 0), yc, xc, min(s * 2, yc + h)
                x1b, y1b, x2b, y2b = w - (x2a - x1a), 0, w, min(y2a - y1a, h)
            elif i == 3:  # bottom right
                x1a, y1a, x2a, y2a = xc, yc, min(xc + w, s * 2), min(s * 2, yc + h)
                x1b, y1b, x2b, y2b = 0, 0, min(w, x2a - x1a), min(y2a - y1a, h)

            img4[y1a:y2a, x1a:x2a] = img[y1b:y2b, x1b:x2b]  # img4[ymin:ymax, xmin:xmax]
            padw = x1a - x1b
            padh = y1a - y1b

            labels_patch = self._update_labels(labels_patch, padw, padh)
            mosaic_labels.append(labels_patch)
        final_labels = self._cat_labels(mosaic_labels)
        final_labels["img"] = img4
        return final_labels