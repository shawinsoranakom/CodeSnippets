def _relabel_formula_boxes(
        cls,
        boxes: List[Dict],
        overlap_threshold: float = 0.7,
    ) -> List[Dict]:
        parent_candidates = [
            box
            for box in boxes
            if (
                not cls._is_formula_box(box)
                and not cls._is_formula_number_box(box)
                and not cls._is_reference_box(box)
            )
        ]

        for box in boxes:
            if not cls._is_formula_box(box):
                continue
            target_label = "display_formula"
            for parent_box in parent_candidates:
                if cls._calculate_cover_ratio(box["bbox"], parent_box["bbox"]) >= overlap_threshold:
                    target_label = "inline_formula"
                    break
            cls._set_formula_label(box, target_label)

        return boxes