def _apply_paddlex_filter_boxes(
        cls,
        boxes: List[Dict],
        drop_inline_formula: bool = True,
    ) -> List[Dict]:
        filtered_boxes = [dict(box) for box in boxes if not cls._is_reference_box(box)]
        dropped_indexes = set()

        for i in range(len(filtered_boxes)):
            if i in dropped_indexes:
                continue
            x1, y1, x2, y2 = filtered_boxes[i]["bbox"]
            width = float(x2) - float(x1)
            height = float(y2) - float(y1)
            if (
                (width < 6.0 or height < 6.0)
                and (drop_inline_formula or not cls._is_inline_formula_box(filtered_boxes[i]))
            ):
                dropped_indexes.add(i)
                continue

            for j in range(i + 1, len(filtered_boxes)):
                if i in dropped_indexes or j in dropped_indexes:
                    continue

                if (
                    not drop_inline_formula
                    and (
                        cls._is_inline_formula_box(filtered_boxes[i])
                        or cls._is_inline_formula_box(filtered_boxes[j])
                    )
                ):
                    continue

                overlap_ratio = cls._calculate_overlap_ratio(
                    filtered_boxes[i]["bbox"],
                    filtered_boxes[j]["bbox"],
                )
                if (
                    drop_inline_formula
                    and (
                        cls._is_inline_formula_box(filtered_boxes[i])
                        or cls._is_inline_formula_box(filtered_boxes[j])
                    )
                ):
                    if overlap_ratio > 0.5:
                        if cls._is_inline_formula_box(filtered_boxes[i]):
                            dropped_indexes.add(i)
                        if cls._is_inline_formula_box(filtered_boxes[j]):
                            dropped_indexes.add(j)
                        continue

                if overlap_ratio > 0.7:
                    box_area_i = cls._calculate_bbox_area(filtered_boxes[i]["bbox"])
                    box_area_j = cls._calculate_bbox_area(filtered_boxes[j]["bbox"])
                    labels = {filtered_boxes[i]["label"], filtered_boxes[j]["label"]}
                    if labels & {"image", "table", "seal", "chart"} and len(labels) > 1:
                        if "table" not in labels or labels <= {"table", "image", "seal", "chart"}:
                            continue
                    if box_area_i >= box_area_j:
                        dropped_indexes.add(j)
                    else:
                        dropped_indexes.add(i)

        kept_boxes = [
            box for index, box in enumerate(filtered_boxes) if index not in dropped_indexes
        ]
        return cls._renumber_indices(kept_boxes)