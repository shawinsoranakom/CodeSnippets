def clip_to_image_size(
        self,
        bounding_boxes,
        height=None,
        width=None,
        bounding_box_format="xyxy",
    ):
        if bounding_box_format not in ("xyxy", "rel_xyxy"):
            raise NotImplementedError
        if bounding_box_format == "xyxy" and (height is None or width is None):
            raise ValueError(
                "`height` and `width` must be set if `format='xyxy'`."
            )

        ops = self.backend
        boxes = bounding_boxes["boxes"]
        labels = bounding_boxes.get("labels", None)
        if width is not None:
            width = ops.cast(width, boxes.dtype)
        if height is not None:
            height = ops.cast(height, boxes.dtype)

        if bounding_box_format == "xyxy":
            x1, y1, x2, y2 = ops.numpy.split(boxes, 4, axis=-1)
            x1 = ops.numpy.clip(x1, 0, width)
            y1 = ops.numpy.clip(y1, 0, height)
            x2 = ops.numpy.clip(x2, 0, width)
            y2 = ops.numpy.clip(y2, 0, height)
            boxes = ops.numpy.concatenate([x1, y1, x2, y2], axis=-1)

            if labels is not None:
                areas = self._compute_area(boxes)
                areas = ops.numpy.squeeze(areas, axis=-1)
                labels = ops.numpy.where(areas > 0, labels, -1)
        elif bounding_box_format == "rel_xyxy":
            x1, y1, x2, y2 = ops.numpy.split(boxes, 4, axis=-1)
            x1 = ops.numpy.clip(x1, 0.0, 1.0)
            y1 = ops.numpy.clip(y1, 0.0, 1.0)
            x2 = ops.numpy.clip(x2, 0.0, 1.0)
            y2 = ops.numpy.clip(y2, 0.0, 1.0)
            boxes = ops.numpy.concatenate([x1, y1, x2, y2], axis=-1)

            if labels is not None:
                areas = self._compute_area(boxes)
                areas = ops.numpy.squeeze(areas, axis=-1)
                labels = ops.numpy.where(areas > 0, labels, -1)

        result = bounding_boxes.copy()
        result["boxes"] = boxes
        if labels is not None:
            result["labels"] = labels
        return result