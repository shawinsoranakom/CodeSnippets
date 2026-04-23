def _deduplicate_boxes_by_iou(
        cls,
        boxes: List[Dict],
        iou_threshold: float = 0.9,
    ) -> List[Dict]:
        if len(boxes) <= 1:
            return boxes

        sorted_candidates = sorted(
            enumerate(boxes),
            key=lambda item: (-float(item[1].get("score", 0.0)), item[0]),
        )
        suppressed_indexes = set()
        kept_indexes = []

        for candidate_pos, (current_index, current_box) in enumerate(sorted_candidates):
            if current_index in suppressed_indexes:
                continue
            kept_indexes.append(current_index)
            for other_index, other_box in sorted_candidates[candidate_pos + 1 :]:
                if other_index in suppressed_indexes:
                    continue
                if cls._calculate_iou(current_box["bbox"], other_box["bbox"]) > iou_threshold:
                    suppressed_indexes.add(other_index)

        kept_indexes.sort()
        return [boxes[index] for index in kept_indexes]