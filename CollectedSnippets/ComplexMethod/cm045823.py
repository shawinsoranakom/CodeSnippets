def _merge_nested_formula_boxes(
        cls,
        boxes: List[Dict],
        overlap_threshold: float = 0.7,
    ) -> List[Dict]:
        if len(boxes) <= 1:
            return boxes

        changed = True
        while changed:
            changed = False
            formula_indexes = [index for index, box in enumerate(boxes) if cls._is_formula_box(box)]
            for formula_pos, left_index in enumerate(formula_indexes):
                for right_index in formula_indexes[formula_pos + 1 :]:
                    left_box = boxes[left_index]
                    right_box = boxes[right_index]
                    if cls._calculate_overlap_ratio(left_box["bbox"], right_box["bbox"]) < overlap_threshold:
                        continue

                    left_area = cls._calculate_bbox_area(left_box["bbox"])
                    right_area = cls._calculate_bbox_area(right_box["bbox"])
                    if left_area > right_area:
                        keep_index, drop_index = left_index, right_index
                    elif right_area > left_area:
                        keep_index, drop_index = right_index, left_index
                    else:
                        left_score = float(left_box.get("score", 0.0))
                        right_score = float(right_box.get("score", 0.0))
                        keep_index, drop_index = (
                            (left_index, right_index)
                            if left_score >= right_score
                            else (right_index, left_index)
                        )

                    keep_box = boxes[keep_index]
                    drop_box = boxes[drop_index]
                    keep_box["bbox"] = cls._union_bbox(keep_box["bbox"], drop_box["bbox"])
                    keep_box["score"] = round(
                        max(float(keep_box.get("score", 0.0)), float(drop_box.get("score", 0.0))),
                        4,
                    )
                    del boxes[drop_index]
                    changed = True
                    break
                if changed:
                    break

        return boxes