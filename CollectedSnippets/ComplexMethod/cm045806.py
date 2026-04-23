def _is_background_picture(
        self,
        picture_entry: _FlattenedShape,
        later_shapes: list[_FlattenedShape],
    ) -> bool:
        picture_bbox = picture_entry.bbox
        if picture_bbox is None:
            return False

        picture_area = self._bbox_area(picture_bbox)
        if picture_area <= 0:
            return False

        overlap_bboxes = []
        for later_shape in later_shapes:
            if not self._is_nonempty_text_shape(later_shape.shape):
                continue

            later_bbox = later_shape.bbox
            if later_bbox is None:
                continue

            overlap_bbox = self._bbox_intersection(picture_bbox, later_bbox)
            if overlap_bbox is not None:
                overlap_bboxes.append(overlap_bbox)

        if not overlap_bboxes:
            return False

        covered_area = self._rectangles_union_area(overlap_bboxes)
        return (
            covered_area / picture_area
            >= BACKGROUND_PICTURE_TEXT_COVERAGE_RATIO
        )